import re
import time
import datetime

import zmq


def now():
    return datetime.datetime.now()

class ZmqClient():
    def __init__(self, conn,):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)

        self.zmq_id = b''.join([b'+',
            re.findall(b'0x[\d\w]*', self.__str__().encode('latin-1'))[0],])
            #',', port_in[15001][0], b':', port_in[15001][1] ])
        self.socket.setsockopt(zmq.IDENTITY, self.zmq_id)
        self.socket.connect(''.join(('tcp://',conn['ip'],':',conn['port'],)))

    def send(self, msg):
        data = (('%s  +/ cl: %s /' %(msg.decode('latin-1'),
                now())).encode('latin-1'))
        self.socket.send_multipart([data])

    def recv(self):
        #  Get the reply.
        [data] = self.socket.recv_multipart()
        yield data


def zmq_cl(conn, msg:list, msg_out:list):
    z = ZmqClient(conn)
    for i in msg:
        z.send(i,)
        msg_out.extend(list(z.recv()))


if __name__ == '__main__':
    conn = {'ip': '127.0.0.1', 'port': '15065'}
    msg_out = []
    z = ZmqClient(conn)
    msg = (b'Hello',)
    for i in msg:
        z.send(i,)
        msg_out = b"".join((msg_out,), z.recv())
    print(msg_out)
