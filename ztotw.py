#! /usr/bin/python3
# -*- coding: utf-8 -*-

import time
import re
import queue
import datetime
import signal
import argparse
import sys
import os

import zmq
from twisted.internet import reactor, protocol, threads


def agrparser():
    parser = argparse.ArgumentParser(
        description=' zmq(port) -> tcp/ip(ip/port) ')
    parser.add_argument("--zp", dest='zmqport',
        type=str, required=True, help='local port')
    parser.add_argument("--rip", dest='remoteip',
        type=str, required=True, help='remote ip')
    parser.add_argument("--rp", dest='remoteport',
        type=str, required=True, help='remote port')
    args = parser.parse_args()
    return args


ZS_PAIR_PORT = "inproc://ztotw"

connection = {}
q_conn = queue.Queue()


#profile handler
def now():
    return datetime.datetime.now()

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



class EchoClient(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
    def connectionMade(self):
        connection[self.factory.connect_id] = self
        # every connect will create dealer
        self.zsocket = self.factory.zmq_handler.context.socket(zmq.DEALER)
        self.zsocket.setsockopt(zmq.IDENTITY, self.factory.frontend_id)
        self.zsocket.connect(ZS_PAIR_PORT)
        self.tcpSend(self.factory.data)
        self.closeTimer  = time.time()

    def dataReceived(self, data):
        self.closeTimer = time.time()
        data = Time.f_f('t.R', data)
        self.zsocket.send_multipart([data,])

    def tcpSend(self, data):
        data = Time.f_f('t.S', data)
        self.transport.write(data)

    def close(self):
        self.zsocket.close()
        connection.pop(self.factory.connect_id)
        # print('Connection close.')
        self.transport.loseConnection()


class EchoFactory(protocol.ClientFactory):
    def __init__(self, zmq_handler, conn, data):
        self.zmq_handler = zmq_handler
        self.frontend_id = conn['frontend_id']
        self.connect_id = b''.join([conn['connect_id'],
            b',', conn['ip'].encode('latin-1'),
            b':', str(conn['port']).encode('latin-1'),])
        self.data = data
    def buildProtocol(self, addr):
        return EchoClient(self)
    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print ("Connection lost.")
        #reactor.stop()


class ZmqHandler():
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.context = zmq.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(''.join(('tcp://',self.conn['ip'],':',self.conn['port'],)))

        # every connect will create dealer
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(ZS_PAIR_PORT)

        self.poll = zmq.Poller()
        self.poll.register(self.frontend, zmq.POLLIN)
        self.poll.register(self.backend, zmq.POLLIN)

        # every connect will create dealer
        connection[b'stop_reactor'] = self
        self.stop_reactor = self.context.socket(zmq.DEALER)
        self.stop_reactor.setsockopt(zmq.IDENTITY, b'stop_reactor')
        self.stop_reactor.connect(ZS_PAIR_PORT)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.frontend.close()
        self.backend.close()



    def run(self):
        reactor.callLater(0.3, self.tcpConnect)
        d = threads.deferToThread(self.read_write)



    def backend_handler(self):
        [zmq_backend_id, data,] = self.backend.recv_multipart()
        if zmq_backend_id == b'stop_reactor':
            raise zmq.ZMQError
        data = Time.f_f('z.R', data)
        self.frontend.send_multipart([zmq_backend_id, b'', data])

    def frontend_handler(self):
        [frontend_id, connect_id, data] = self.frontend.recv_multipart()
        data = Time.f_f('z.P', data)
        if connect_id and connect_id in connection:
            data = Time.f_f('ztC', data)
            if connection.get(connect_id):
                 connection[connect_id].tcpSend(data)
        elif connect_id:
            # get conn['server'] from packet header -> connect_id
            conn = {}

            conn['connect_id'], conn['ip'], conn['port'], = \
                (re.findall(b'0x[\d\w]*', connect_id)[0],
                b'.'.join(re.findall(b'(?<=[,.])\d+',connect_id)).decode('latin-1'),
                int(re.findall(b'(?<=:)\d+', connect_id)[0]),
                )
            conn['frontend_id'] = frontend_id
            q_conn.put((conn, data,))
        else:
            pass


    def read_write(self):
        # t = time.time()
        # i = 0
        # print('start')
        while True:
                sockets = dict(self.poll.poll())
                if self.frontend in sockets:
                    if sockets[self.frontend] == zmq.POLLIN:
                        self.frontend_handler()
                        # i += 1
                # if time.time() - 1 > t:
                #    t += 1
                #    # print('send / s = ', end= '')
                #    # print(i)
                #    i = 0
                if self.backend in sockets:
                    if sockets[self.backend] == zmq.POLLIN:
                        try:
                            self.backend_handler()
                        except zmq.ZMQError:
                            break
        reactor.stop()
        return 0


    def tcpConnect(self):
        if not q_conn.empty():
            conn, data = q_conn.get()
            reactor.connectTCP(conn['ip'], conn['port'],
                EchoFactory(self, conn, data))
        reactor.callLater(0.3, self.tcpConnect)
        return 0


def signal_handler(signum, frame):
    connection[b'stop_reactor'].stop_reactor.send_multipart([b'',])



def main(conn):
    with ZmqHandler(conn) as zmq_handler:
        zmq_handler.run()
        reactor.run()
    print('stop')
    sys.exit(0)


def z_to_tw(conn):
    signal.signal(signal.SIGTERM, signal_handler)
    main(conn)


if __name__ == '__main__':

    args = agrparser()

    connzc = {'ip': '127.0.0.1', 'port': args.zmqport,
        'remote': {'ip': args.remoteip, 'port': args.remoteport} }

    conn = {}
    print('wait')
    for d, k in zip((connzc,), ('zc',)):
        conn[k] = d
        os.system('fuser -k '+d['port']+'/tcp')
        if d.get('remote'):
            os.system('fuser -k '+d['remote']['port']+'/tcp')
    print(conn)
    print('start')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGQUIT, signal_handler)
    main(conn['zc'])
