#! /usr/bin/python3
# -*- coding: utf-8 -*-

import time
import datetime
import re
import signal
import argparse
import os
import sys
import traceback

import zmq
from twisted.internet import reactor, protocol, threads
import twisted.internet.error


ZS_PAIR_PORT = "inproc://ps"
connection = {}

def now():
    return datetime.datetime.now()


def agrparser():
    parser = argparse.ArgumentParser(
        description=' tcp/ip(port) -> zmq(port) -> tcp/ip(ip/port) ')
    parser.add_argument("--lp", dest='localport',
        type=str, required=True, help='local port')
    parser.add_argument("--zp", dest='zmqport',
        type=str, required=True, help='remote zmq port')
    parser.add_argument("--rip", dest='remoteip',
        type=str, required=True, help='remote ip')
    parser.add_argument("--rp", dest='remoteport',
        type=str, required=True, help='remote port')
    args = parser.parse_args()
    return args


class Time():
    def __init__(self):
        pass
    def f_f(name, data):
        return ('%s  +/ %s: %s /' %
                (data.decode('latin-1'),
                 name, now())).encode('latin-1')
    def f_f(name, data):
        return ('%s  -/ %s: %s /' %
                (data.decode('latin-1'),
                 name, now())).encode('latin-1')



class Echo(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.d = b''
        self.data = b''
        self.zs_port = self.factory.zs_port

    def connectionMade(self):
        self.zmq_client_id = b''.join([b'+', re.findall(
            b'0x[\d\w]*',
            self.__str__().encode('latin-1'))[0],
            (b''.join([
                b',', self.factory.conn['remote']['ip'].encode('latin-1'),
                b':', self.factory.conn['remote']['port'].encode('latin-1'),
                ])
                if self.factory.conn.get('remote') else b'')
            ])
        # print(self.zmq_client_id)
        connection[self.zmq_client_id] = self
        #print('connection = ', end='')
        #print(connection)
        # every connect will create dealer
        self.frontend = self.factory.zmq_handler.context.socket(zmq.DEALER)
        self.frontend.setsockopt(zmq.IDENTITY, self.zmq_client_id)
        self.frontend.connect(self.zs_port)
        #self.closeTimer  = time.time()
        #reactor.callLater(3, self.isClose)
        #self.isCl = False

    def dataReceived(self, data):
        self.closeTimer = time.time()
        self.frontend.send_multipart([data])

    def tcpSend(self, data):
        #print('tcpSend = ',end='')
        #print(data)
        if data == b'/x00': self.isCl = True
        self.transport.write(data)

    def isClose(self):
        if (self.closeTimer + 3 < time.time()) or self.isCl:
            self.close()
        else:
            reactor.callLater(3, self.isClose)
        return 0

    def close(self):
        data = b'/x00'
        self.frontend.send_multipart([data])
        self.frontend.close()
        connection.pop(self.zmq_client_id)
        # print('Connection close.  ', end='')
        self.transport.loseConnection()
        # print('connection = ', end='')
        # print(connection)


class EchoFactory(protocol.Factory):
    def __init__(self, handle_error, conn, zmq_handler):
        self.handle_error = handle_error
        self.conn = conn
        self.zmq_handler = zmq_handler
        connection[b'0'] = self
        self.frontend = self.zmq_handler.context.socket(zmq.DEALER)
        self.frontend.setsockopt(zmq.IDENTITY, b'0')
        self.zs_port = ZS_PAIR_PORT
        self.frontend.connect(self.zs_port)
    def buildProtocol(self, addr):
        # print('Echo = ', end='')
        # print(addr)
        return Echo(self)
    def clientConnectionFailed(self, connector, reason):
        # print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        # print ("Connection lost.")
        reactor.stop()


class ZmqHandler():
    def __init__(self, handle_error, conn):
        self.handle_error = handle_error
        self.conn_backend = conn
        self.conn_frontend = ZS_PAIR_PORT

    def __enter__(self):

       self.context = zmq.Context()
       self.backend = self.context.socket(zmq.DEALER)
       self.backend.setsockopt(zmq.IDENTITY, b'0')
       self.backend.connect(''.join((
           'tcp://',self.conn_backend['ip'],':',self.conn_backend['port'],)))
       # every connect will create dealer
       self.frontend = self.context.socket(zmq.ROUTER)
       self.frontend.bind(self.conn_frontend)
       self.poll = zmq.Poller()
       self.poll.register(self.backend, zmq.POLLIN)
       self.poll.register(self.frontend, zmq.POLLIN)
       return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print ('zmq close()')
        self.frontend.close()
        self.backend.close()


    def run(self):
        threads.deferToThread(self.read_write)


    def backend_handler(self):
        # print('backend_handler')
        [zmq_backend_id, data] = self.backend.recv_multipart()
        data = Time.f_f('z.P', data)
        # print('backend_recv = ',end ='')
        # print(zmq_backend_id, data)
        if connection.get(zmq_backend_id):
             connection[zmq_backend_id].tcpSend(data)
        # print('backend_send = ',end='')
        # print(zmq_backend_id, data)


    def frontend_handler(self):
        # print('frontend_handler')
        zmq_frontend_id, data = self.frontend.recv_multipart()
        # print(zmq_frontend_id)
        # print(data)
        if zmq_frontend_id == b'0':
            print('zmq.ZMQError')
            raise zmq.ZMQError
        #print('frontend_recv = ',end ='')
        #print(zmq_frontend_id, data)
        self.backend.send_multipart([zmq_frontend_id, data])
        #print('frontend_send = ',end='')
        #print(zmq_frontend_id, data)

    def read_write(self):
        t = time.time()
        i = 0
        while True:
            now = time.time()
            sockets = dict(self.poll.poll())
            if self.backend in sockets:
                if sockets[self.backend] == zmq.POLLIN:
                    self.backend_handler()
            if time.time() - 1 > t:
                t += 1
                # print('send / s = ', end= '')
                # print(i)
                i = 0
            if self.frontend in sockets:
                if sockets[self.frontend] == zmq.POLLIN:
                    i += 1
                    try:
                        self.frontend_handler()
                    except zmq.ZMQError:
                        # print('break')
                        break
        # print('reactor.stop from zmq thread')
        reactor.stop()
        return 0




def signal_handler(signum, frame):
    # print('terminate twtoz')
    # print(connection)
    connection[b'0'].frontend.send_multipart([b''])

def main(conn):
    with ZmqHandler(True, conn['zs']) as zmq_handler:
        zmq_handler.run()
        reactor.listenTCP(int(conn['tc']['port']),
            EchoFactory(True, conn['tc'], zmq_handler))
        # print('reactor.run()')
        reactor.run()
    sys.exit(0)


def tw_to_z(conn):
    signal.signal(signal.SIGTERM, signal_handler)
    main(conn)


if __name__ == '__main__':

    args = agrparser()

    conntc = {'ip': '127.0.0.1', 'port': args.localport}
    connzs = {'ip': '127.0.0.1', 'port': args.zmqport}
    conn = {}
    print('wait')
    for d, k in zip((conntc, connzs), ('tc', 'zs')):
        conn[k] = d
        os.system('fuser -k '+d['port']+'/tcp')
    print(conn)
    print('start')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGQUIT, signal_handler)
    main(conn)
