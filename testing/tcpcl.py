#! /usr/local/bin/python3
# -*- coding: utf-8 -*-

import datetime
import socket


def now():
    return datetime.datetime.now()

class MyTCPClient():
    def __init__(self, conn,):
        self.conn = conn
    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.conn['ip'], int(self.conn['port'])))
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def send(self, msg):
        data = ('%s  +/ cl: %s /' %(msg.decode('latin-1'),
                now())).encode('latin-1')
        self.sock.sendall(data)

    def recv(self):
        #  Get the reply.
        data = self.sock.recv(1024)
        yield data


def tcp_cl(conn, msg:list, msg_out:list):
    with MyTCPClient(conn) as z:
        for i in msg:
            z.send(i)
            msg_out.extend(list(z.recv()))
        z.send(b'')


if __name__ == '__main__':
    conn = {'ip': '127.0.0.1', 'port': '15075'}
    msg_out = []
    with MyTCPClient(conn) as z:
        msg = (b'Hello',)
        for msg_ in msg:
            z.send(msg_,)
            msg_out = b"".join((msg_out,),z.recv())
    print(msg_out)
