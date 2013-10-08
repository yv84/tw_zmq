import io
import sys
import os
import time
from subprocess import Popen
from multiprocessing import Process, Manager


import unittest

#import zasync
import testing.zmqcl as zmqcl
import testing.zmqserv as zmqserv
import testing.tcpserv as tcpserv
import testing.tcpcl as tcpcl


class TwzmqTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("time")
    def test_run1(self):
        self.assertRegex("abc", "\w{3}")

    def test_run2(self):
        conn = {'ip': '127.0.0.1', 'port': '15067'}
        test_msg = (b'test', b'test2', b'test3')
        N = 10
        manager = Manager()
        ls = manager.list(test_msg)
        ls_out = manager.list()
        dc = manager.dict(conn)
        os.system('fuser -k '+conn['port']+'/tcp')
        processes = [Process(target=zmqserv.zmq_serv, args=(dc,)),]
        for i in range(N):
            processes.append(Process(target=zmqcl.zmq_cl, args=(dc, ls, ls_out,)))

        processes[0].start()
        time.sleep(0.1)
        for p in processes[1:]:
            p.start()

        now = time.time()
        while N != len(ls_out) and \
          (now+30 > time.time()):
            time.sleep(1)
        print("zmq = %.3f" %(time.time() - now))

        processes.reverse()
        for p in processes:
            p.terminate()
            p.join()

        os.system('fuser -k '+conn['port']+'/tcp')
        #print(ls_out)
        print('zmq msg count %i' %len(ls_out))
        self.assertTrue(N*len(test_msg) == len(ls_out))


    def test_run3(self):

        conn = {'ip': '127.0.0.1', 'port': '15079'}
        test_msg = (b'test', b'test2', b'test3')
        N = 10
        manager = Manager()
        ls = manager.list(test_msg)
        ls_out = manager.list()
        dc = manager.dict(conn)
        os.system('fuser -k '+conn['port']+'/tcp')
        processes = [Process(target=tcpserv.tcp_serv, args=(dc,)),]
        for i in range(N):
            processes.append(Process(target=tcpcl.tcp_cl, args=(dc, ls, ls_out,)))

        processes[0].start()
        time.sleep(0.1)
        for p in processes[1:]:
            p.start()

        now = time.time()
        while N*len(test_msg) != len(ls_out) and \
          (now+30 > time.time()):
            time.sleep(1)
        print("tcp = %.3f" %(time.time() - now))
        
        processes.reverse()
        for p in processes:
            p.terminate()
            p.join()

        os.system('fuser -k '+conn['port']+'/tcp')
        #print(ls_out)
        print('tcp msg count %i' %len(ls_out))
        self.assertTrue(N*len(test_msg) == len(ls_out))



if __name__ == '__main__':
    unittest.main()
