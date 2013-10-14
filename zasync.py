#! /usr/bin/python3
# -*- coding: utf-8 -*-

import threading
import time
import datetime
from random import choice
import signal
import argparse
import os
import sys

import zmq


def agrparser():
    parser = argparse.ArgumentParser(
        description=' zmq(port) -> zmq(port) ')
    parser.add_argument("--lp", dest='localport',
        type=str, required=True, help='local port')
    parser.add_argument("--rp", dest='remoteport',
        type=str, required=True, help='remote port')
    args = parser.parse_args()
    return args


class ZmqHandler():
    """ServerTask"""
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.context = zmq.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(''.join(
            ('tcp://',self.conn['zc']['ip'],':',self.conn['zc']['port'],)))

        self.backend = self.context.socket(zmq.DEALER)
        self.backend.setsockopt(zmq.IDENTITY, b'0')
        self.backend.connect(''.join(
            ('tcp://',self.conn['zs']['ip'],':',self.conn['zs']['port'],)))

        self.poll = zmq.Poller()
        self.poll.register(self.frontend, zmq.POLLIN)
        self.poll.register(self.backend,  zmq.POLLIN)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.frontend.close()
        self.backend.close()

    def run(self):
        self.read_write()

    def backend_handler(self): # DEALER
        [connect_id, data] = self.backend.recv_multipart()
        #print ('Sending to frontend  %s | %s\n' % (connect_id, data))
        self.frontend.send_multipart([b'0', connect_id, data])

    def frontend_handler(self): # ROUTER
        [frontend_id, connect_id, data] = self.frontend.recv_multipart()
        #print ('frontend received %s id %s | %s \n' % (frontend_id, connect_id, data))
        self.backend.send_multipart([connect_id, data])

    def read_write(self):
        while True:
            try:
                sockets = dict(self.poll.poll())
                if self.frontend in sockets:
                    if sockets[self.frontend] == zmq.POLLIN:
                        self.frontend_handler()
                if self.backend in sockets:
                    if sockets[self.backend] == zmq.POLLIN:
                        self.backend_handler()
            except zmq.core.error.ZMQError as e:
                print(e)
                break
        return 0

def signal_handler(signum, frame):
    pass

def main(conn):
    """main function"""
    with ZmqHandler(conn) as zmq_handler:
        zmq_handler.run()
    print('stop')
    sys.exit(0)


def z_async(conn):
    signal.signal(signal.SIGINT, signal_handler)
    main(conn)


if __name__ == '__main__':

    args = agrparser()

    connzc = {'ip': '127.0.0.1', 'port': args.localport}
    connzs = {'ip': '127.0.0.1', 'port': args.remoteport}
    conn = {}
    print('wait')
    for d, k in zip((connzc, connzs), ('zc','zs')):
        conn[k]  = d
        os.system('fuser -k '+d['port']+'/tcp')
    print(conn)
    print('start')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGQUIT, signal_handler)
    main(conn)
