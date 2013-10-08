import time

import zmq

def now():
    return time.ctime(time.time())

class ZmqServ():
    def __init__(self, conn):
        self.context = zmq.Context()
        self.conn = conn
        self.socket = self.context.socket(zmq.ROUTER)
        #self.socket.setsockopt(zmq.IDENTITY, b'1')
        self.cnn = ''.join(('tcp://',conn['ip'],':',conn['port'],))
        print(self.cnn)
        self.socket.bind(self.cnn)

        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def run(self):
        while True:
            socks = dict(self.poller.poll())
            if socks.get(self.socket) == zmq.POLLIN:
                [address, message ] = self.socket.recv_multipart()
                self.socket.send_multipart([address,
                    ('Echo disp hw=>%s at %s' % (message,
                        now())).encode('latin-1')])

if __name__ == '__main__':
    conn = {'ip': '127.0.0.1', 'port': '15065'}
    z = ZmqServ(conn)
    z.run()
