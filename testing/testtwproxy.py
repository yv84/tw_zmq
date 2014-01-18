import io
import sys
import os
import time
from subprocess import Popen
from multiprocessing import Process, Manager, JoinableQueue


import unittest

import twproxy

import testing.tcpserv as tcpserv
import testing.tcpcl as tcpcl


class TwzmqTestCase(unittest.TestCase):

    def setUp(self):
        self.port1 = '15067'
        self.port2 = '15068'
        self.port3 = '15069'
        self.test_msg = (b'test', b'test2', b'test3')

    def tearDown(self):
        pass


    def test_tcpc_tcps(self):

        conn = {'ip': '127.0.0.1', 'port': self.port1}
        N = 10
        manager = Manager()
        ls = manager.list(self.test_msg)
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
        while N*len(self.test_msg) != len(ls_out) and \
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
        self.assertTrue(N*len(self.test_msg) == len(ls_out))


    def test_tcpc_twproxy_tcps(self):

        conn = {
            'client': {'ip': '127.0.0.1', 'port':  self.port1}, # client -> tw_proxy
            'server': {'ip': '127.0.0.1', 'port':  self.port2},  # proxy -> tw_server
            } 
        N = 10
        manager = Manager()
        ls = manager.list(self.test_msg)
        ls_out = manager.list()

        dc = {}

        for d, k in zip([c for c in conn], [conn[c] for c in conn]):
            dc[d]  = manager.dict(k)
            os.system('fuser -k '+conn[d]['port']+'/tcp')

        processes = []
        processes.append(Process(target=tcpserv.tcp_serv, args=(dc['server'],))) # server
        proxy_args = {'port_in': self.port1, 'ip_out': '127.0.0.1',
            'port_out': self.port2, 'pprefix': ''}
        processes.append(Process(target=twproxy.main, args=(proxy_args,)))          # proxy
        for i in range(N):
            processes.append(Process(target=tcpcl.tcp_cl, args=(dc['client'], ls, ls_out,))) # N clients

        processes[0].start()
        processes[1].start()
        time.sleep(0.1)
        for p in processes[2:]:
            p.start()
            time.sleep(0.1)

        now = time.time()
        while N*len(self.test_msg) != len(ls_out) and \
          (now+2 > time.time()):
            time.sleep(1)
        print("tcp = %.3f" %(time.time() - now))

        processes.reverse()
        for p in processes:
            p.terminate()
            p.join()

        for d, k in zip([c for c in conn], [conn[c] for c in conn]):
            os.system('fuser -k '+conn[d]['port']+'/tcp')

        #print(ls_out)
        print('tcp msg count %i' %len(ls_out))
        self.assertTrue(N*len(self.test_msg) == len(ls_out))



if __name__ == '__main__':
    unittest.main()
