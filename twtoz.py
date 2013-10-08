import time
import datetime
import re
import signal
import argparse

import zmq
from twisted.internet import reactor, protocol, threads


ZS_PAIR_PORT = "inproc://ps"
conn = {}

def now():
    return datetime.datetime.now()

class handler():
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
        self.zs_port = ZS_PAIR_PORT

    def connectionMade(self):
        self.id_zmq = b''.join([b'+', re.findall(
            b'0x[\d\w]*',
            self.__str__().encode('latin-1'))[0],
            b',', self.factory.ip_out.encode('latin-1'),
            b':', self.factory.port_out.encode('latin-1')])
        conn[self.id_zmq] = self
        print('conn = ', end='')
        print(conn)
        print('self.id_zmq  = ', end = '')
        print(self.id_zmq)
        # every connect will create dealer
        self.frontend = self.factory.zmq_handler.context.socket(zmq.DEALER)
        self.frontend.setsockopt(zmq.IDENTITY, self.id_zmq)
        self.frontend.connect(self.zs_port)
        self.closeTimer  = time.time()
        reactor.callLater(3, self.isClose)
        self.isCl = False

    def dataReceived(self, data):
        self.closeTimer = time.time()
        self.frontend.send_multipart([data])

    def TCPSend(self, data):
        print('TCPSend = ',end='')
        print(data)
        if data == b'/x00': self.isCl = True
        self.transport.write(data)

    def isClose(self):
        if (self.closeTimer + 3 < time.time()) or self.isCl:
            self.close()
        else:
            reactor.callLater(3, self.isClose)
        return 0

    def close(self):
        #def close_zmq(id_zmq):
        data = b'/x00'
        #self.frontend.send(data)
        self.frontend.send_multipart([data])
        self.frontend.close()
        print('conn = ', end='')
        print(conn)
        print('self.id_zmq  = ', end = '')
        print(self.id_zmq)
        conn.pop(self.id_zmq)
        print('Connection close.')
        self.transport.loseConnection()
        print('conn = ', end='')
        print(conn)
        del self.factory
        del self


class EchoFactory(protocol.Factory):
    def __init__(self, connts, zmq_handler):
        self.ip_out = connts['ip']
        self.port_out = connts['port']
        self.zmq_handler = zmq_handler
    def buildProtocol(self, addr):
        return Echo(self)
    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print ("Connection lost.")
        reactor.stop()
        #self.z_socket.disconnect()
        #reactor.stop()


def zmqerror(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except zmq.core.error.ZMQError as e:
                print(e)
            return
        return wrapper

class Zmq_handler():
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
        print('reactor stop')
        reactor.stop()
        print ('zmq close()')
        frontend.close()
        backend.close()

    def run(self):
        d = threads.deferToThread(self.read_write)

    def backend_handler(self):
        #print('backend_handler')
        [zmq_id, data] = self.backend.recv_multipart()
        data = handler.f_f('z.P', data)
        #print('backend_recv = ',end ='')
        #print(zmq_id, data)
        if conn.get(zmq_id):
             conn[zmq_id].TCPSend(data)
        #print('backend_send = ',end='')
        #print(zmq_id, data)


    def frontend_handler(self):
        #print('frontend_handler')
        zmq_id, data = self.frontend.recv_multipart()
        #print('frontend_recv = ',end ='')
        #print(zmq_id, data)
        self.backend.send_multipart([zmq_id, data])
        #print('frontend_send = ',end='')
        #print(zmq_id, data)


    @zmqerror
    def read_write(self):
        t = time.time()
        i = 0
        while True:
            sockets = dict(self.poll.poll())
            if self.backend in sockets:
                if sockets[self.backend] == zmq.POLLIN:
                    self.backend_handler()
            if time.time() - 1 > t:
                t += 1
                print('send / s = ', end= '')
                print(i)
                i = 0
            if self.frontend in sockets:
                if sockets[self.frontend] == zmq.POLLIN:
                    i += 1
                    self.frontend_handler()




def signal_handler(signum, frame):
    print('interrupted')
signal.signal(signal.SIGINT, signal_handler)

def main(conn):
    with Zmq_handler(conn['zs']) as zmq_handler:
        zmq_handler.run()
        #for p_in in port_in.items():
        reactor.listenTCP(int(conn['tc']['port']), EchoFactory(conn['ts'], zmq_handler))
        reactor.run()


def tw_to_z(conn):
    main(conn)







if __name__ == '__main__':

    #argparse

    parser = argparse.ArgumentParser(
        description=' tcp/ip(port) -> zmq(port) -> tcp/ip(ip/port) ')
    parser.add_argument("--lp", dest='localport',
        type=int, required=True, help='local port')
    parser.add_argument("--zp", dest='zmqport',
        type=int, required=True, help='remote zmq port')
    parser.add_argument("--rip", dest='remoteip',
        type=str, required=True, help='remote ip')
    parser.add_argument("--rp", dest='remoteport',
        type=int, required=True, help='remote port')

    args = parser.parse_args()

    port_in = {args.localport: (
        (args.remoteip).encode('latin-1'),
        (str(args.remoteport)).encode('latin-1') )}
    port_zmq = "tcp://*:" + str(args.zmqport)
    zs_port = "inproc://ps"


    main(conn) #?
