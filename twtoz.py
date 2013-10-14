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
        connection[self.zmq_client_id] = self
        self.frontend = self.factory.zmq_handler.context.socket(zmq.DEALER)
        self.frontend.setsockopt(zmq.IDENTITY, self.zmq_client_id)
        self.frontend.connect(self.zs_port)

    def dataReceived(self, data):
        self.frontend.send_multipart([data])

    def tcpSend(self, data):
        self.transport.write(data)


class EchoFactory(protocol.Factory):
    def __init__(self, conn, zmq_handler):
        self.conn = conn
        self.zmq_handler = zmq_handler
        connection[b'stop_reactor'] = self
        self.frontend = self.zmq_handler.context.socket(zmq.DEALER)
        self.frontend.setsockopt(zmq.IDENTITY, b'stop_reactor')
        self.zs_port = ZS_PAIR_PORT
        self.frontend.connect(self.zs_port)
    def buildProtocol(self, addr):
        return Echo(self)
    def clientConnectionFailed(self, connector, reason):
        # print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        # print ("Connection lost.")
        reactor.stop()


class ZmqHandler():
    def __init__(self, conn):
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
        self.frontend.close()
        self.backend.close()

    def run(self):
        threads.deferToThread(self.read_write)

    def backend_handler(self): # DEALER
        [zmq_backend_id, data] = self.backend.recv_multipart()
        data = Time.f_f('z.P', data)
        if connection.get(zmq_backend_id):
             connection[zmq_backend_id].tcpSend(data)

    def frontend_handler(self): # ROUTER
        zmq_frontend_id, data = self.frontend.recv_multipart()
        if zmq_frontend_id == b'stop_reactor':
            raise zmq.ZMQError
        self.backend.send_multipart([zmq_frontend_id, data])

    def read_write(self):
        while True:
            now = time.time()
            sockets = dict(self.poll.poll())
            if self.backend in sockets:
                if sockets[self.backend] == zmq.POLLIN:
                    self.backend_handler()
            if self.frontend in sockets:
                if sockets[self.frontend] == zmq.POLLIN:
                    try:
                        self.frontend_handler()
                    except zmq.ZMQError:
                        break
        reactor.stop()
        return 0


def signal_handler(signum, frame):
    connection[b'stop_reactor'].frontend.send_multipart([b'',])

    
def main(conn):
    with ZmqHandler(conn['zs']) as zmq_handler:
        zmq_handler.run()
        reactor.listenTCP(int(conn['tc']['port']),
            EchoFactory(conn['tc'], zmq_handler))
        reactor.run()
    print('stop')
    sys.exit(0)


def tw_to_z(conn):
    signal.signal(signal.SIGTERM, signal_handler)
    main(conn)


if __name__ == '__main__':

    args = agrparser()

    conntc = {'ip': '127.0.0.1', 'port': args.localport,
        'remote': {'ip': args.remoteip, 'port': args.remoteport} }
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

