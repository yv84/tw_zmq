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


class twzmqTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("time")
    def test_run1(self):
        pass

    def test_run2(self):
        def zmq_serv(conn):
            z = zmqserv.ZmqServ(conn)
            z.run()

        def zmq_cl(conn, msg:list, msg_out:list):
            z = zmqcl.ZmqClient(conn)
            z.send(msg)
            msg_out.extend(list(z.rcv()))
    
        conn = {'ip': '127.0.0.1', 'port': '15066'}
        test_msg = (b'test',)
        manager = Manager()
        ls = manager.list(test_msg)
        ls_out = manager.list()
        dc = manager.dict(conn)
        os.system('fuser -k '+conn['port']+'/tcp')
        processes = [Process(target=zmq_serv, args=(dc,)),]
        for i in range(20):
            processes.append(Process(target=zmq_cl, args=(dc, ls, ls_out,)))

        for p in processes:
            p.start()
            time.sleep(0.1)

        processes.reverse()
        for p in processes:
            p.terminate()
            p.join()

        os.system('fuser -k '+conn['port']+'/tcp')
        print(ls_out)
        self.assertTrue(ls_out)


    def test_run3(self):
        self.assertRegex("abc", "\w{3}")



if __name__ == '__main__':
    unittest.main()
