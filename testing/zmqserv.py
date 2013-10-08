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
                [zmq_id, address, message ] = self.socket.recv_multipart()
                self.socket.send_multipart([zmq_id, address,
                    ('Echo disp hw=>%s at %s' % (message,
                        now())).encode('latin-1')])

def zmq_serv(conn):
    z = ZmqServ(conn)
    z.run()


if __name__ == '__main__':
    conn = {'ip': '127.0.0.1', 'port': '15065'}
    z = ZmqServ(conn)
    z.run()
 
