import io
import sys
import os
import time
from subprocess import Popen
from multiprocessing import Process, Manager, JoinableQueue


import unittest

import twtoz
import ztotw
import testing.zmqcl as zmqcl
import testing.zmqserv as zmqserv
import testing.tcpserv as tcpserv
import testing.tcpcl as tcpcl


class TwzmqTestCase(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self):
        pass


    #@unittest.skip("time")
    #def test_run1(self):
    #    self.assertRegex("abc", "\w{3}")


    def test_zmqc_zmqs(self):
        conn = {'ip': '127.0.0.1', 'port': '15067',
            'remote': {'ip': '127.0.0.1', 'port': '15085'}}
        test_msg = (b'test', b'test2', b'test3')
        N = 1
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
            time.sleep(0.1)

        now = time.time()
        while N*len(test_msg) != len(ls_out) and \
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


    def test_tcpc_tcps(self):

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
            time.sleep(0.1)

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


    def test_tcpc_TwtoZ_zmqs(self):
        conntc = {'ip': '127.0.0.1', 'port': '15094',
            'remote': {'ip': '127.0.0.1', 'port': '15095'} }
        connzs = {'ip': '127.0.0.1', 'port': '15096'}
        test_msg = (b'test', b'test2' )
        N = 5
        manager = Manager()
        ls = manager.list(test_msg)
        ls_out = manager.list()
        dc = {}
        for d, k in zip((conntc, connzs), ('tc', 'zs')):
            dc[k]  = manager.dict(d)
            os.system('fuser -k '+d['port']+'/tcp')

        processes = []
        processes.append(Process(target=zmqserv.zmq_serv, args=(dc['zs'],)))
        processes.append(Process(target=twtoz.tw_to_z,
                args=(dc,)))
        for i in range(N):
            processes.append(Process(target=tcpcl.tcp_cl,
                args=(dc['tc'], ls, ls_out,)))

        for p in processes[:2]:
            p.start()
        time.sleep(0.5)
        for p in processes[2:]:
            p.start()
            time.sleep(0.1)

        now = time.time()
        while N*len(test_msg) != len(ls_out) and \
          (now+10 > time.time()):
            time.sleep(1)
        print("zmq = %.3f" %(time.time() - now))

        processes.reverse()
        for p in processes[:-3]:
            p.terminate()
            p.join()
        processes[-1].terminate()
        processes[-1].join()

        #print(processes)

        for conn in (conntc, connzs):
            os.system('fuser -k '+conn['port']+'/tcp')
        #print(ls_out)
        print('twtoz msg count %i' %len(ls_out))
        self.assertTrue(N*len(test_msg) == len(ls_out))




    #@unittest.skip("time")
    def test_zmqc_ZtoTw_tcps(self):

        connzc = {'ip': '127.0.0.1', 'port': '15091',
            'remote': {'ip': '127.0.0.1', 'port': '15092'}}
        test_msg = (b'test', b'test2', b'test3')
        N = 1
        manager = Manager()
        ls = manager.list(test_msg)
        ls_out = manager.list()
        dc = {}

        for d, k in zip((connzc,), ('zc',)):
            dc[k]  = manager.dict(d)
            os.system('fuser -k '+d['port']+'/tcp')
            if d.get('remote'):
                os.system('fuser -k '+d['remote']['port']+'/tcp')

        processes = []
        processes.append(Process(target=tcpserv.tcp_serv, args=(dc['zc']['remote'],)))
        processes.append(Process(target=ztotw.z_to_tw,
                args=(dc['zc'],)))
        for i in range(N):
            processes.append(Process(target=zmqcl.zmq_cl,
                args=(dc['zc'], ls, ls_out,)))

        for p in processes[:2]:
            p.start()
        time.sleep(0.1)
        for p in processes[2:]:
            p.start()
            time.sleep(0.1)

        now = time.time()
        while N*len(test_msg) != len(ls_out) and \
          (now+30 > time.time()):
            time.sleep(1)
        print("zmq = %.3f" %(time.time() - now))

        processes.reverse()
        for p in processes[:-3]:
            p.terminate()
            p.join()
        processes[-1].terminate()
        processes[-1].join()
        print(processes)

        for conn in (connzc,):
            os.system('fuser -k '+conn['port']+'/tcp')
            if d.get('remote'):
                os.system('fuser -k '+d['remote']['port']+'/tcp')
        print(ls_out)
        print('twtoz msg count %i' %len(ls_out))
        self.assertTrue(N*len(test_msg) == len(ls_out))








if __name__ == '__main__':
    unittest.main()
