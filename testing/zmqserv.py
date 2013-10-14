import datetime

import zmq


def now():
    return datetime.datetime.now()

class ZmqServ():
    def __init__(self, conn):
        self.context = zmq.Context()
        self.conn = conn
        self.socket = self.context.socket(zmq.ROUTER)
        #self.socket.setsockopt(zmq.IDENTITY, b'1')
        self.socket.bind(''.join(('tcp://',conn['ip'],':',conn['port'],)))

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def run(self):
        while True:
            socks = dict(self.poller.poll())
            if socks.get(self.socket) == zmq.POLLIN:
                self.send(self.recv())

    def send(self, args):
        self.socket.send_multipart([args[0], args[1],
             ('Echo disp hw=>%s at %s' % (args[2],
                now())).encode('latin-1')])

    def recv(self):
        args = []
        args.extend(self.socket.recv_multipart())
        return args

def zmq_serv(conn):
    print(conn)
    z = ZmqServ(conn)
    z.run()


if __name__ == '__main__':
    conn = {'ip': '127.0.0.1', 'port': '15065'}
    z = ZmqServ(conn)
    z.run()
