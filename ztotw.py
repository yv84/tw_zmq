import time
import re
import queue
import datetime
import signal
import argparse

import zmq
from twisted.internet import reactor, protocol, threads


parser = argparse.ArgumentParser(description=' zmq(port) -> tcp/ip(ip/port) ')
parser.add_argument("--lp", dest='localport', type=int, required=True,
                   help='local port')
parser.add_argument("--rip", dest='remoteip', type=str, required=True,
                   help='remote ip')
parser.add_argument("--rp", dest='remoteport', type=int, required=True,
                   help='remote port')

args = parser.parse_args()




ip_out = args.remoteip
#port_out = args.remoteport
zmq_in = "tcp://*:" + str(args.localport)
#ip_out, port_out = "localhost" , 15011
#zmq_in = 'tcp://*:15062'
zbackend = "inproc://ps"

conn = {}
q_conn = queue.Queue()


#profile handler
def now():                             
    return datetime.datetime.now()

class handler():
    def __init__(self):
        pass
    def f_f(name, data):
        return ('%s  +/ %s: %s /' % (data.decode('latin-1'), name, now())).encode('latin-1')
    def f_f(name, data):
        return ('%s  -/ %s: %s /' % (data.decode('latin-1'), name, now())).encode('latin-1')



class EchoClient(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
    def connectionMade(self):
        conn[self.factory.id_zmq] = self
        self.zsocket = context.socket(zmq.DEALER) # every connect will create dealer
        self.zsocket.setsockopt(zmq.IDENTITY, self.factory.id_zmq)
        self.zsocket.connect(zbackend)
        print(conn)
        self.TCPSend(self.factory.data)
        self.closeTimer  = time.time()
        reactor.callLater(3, self.isClose)
        self.isCl = False

    def dataReceived(self, data):
        self.closeTimer = time.time()
        data = handler.f_f('t.R', data)
        self.zsocket.send_multipart([data,])

    def TCPSend(self, data):
        if data == b'/x00': self.isCl = True
        data = handler.f_f('t.S', data)
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
        #self.ps.send(data)
        self.zsocket.send_multipart([data])
        self.zsocket.close()
        print('conn = ', end='')
        print(conn)
        print('self.id_zmq  = ', end = '')
        print(self.factory.id_zmq)  
        conn.pop(self.factory.id_zmq)
        print('Connection close.')
        self.transport.loseConnection()
        print('conn = ', end='')
        print(conn)
        del self.factory
        del self
    
class EchoFactory(protocol.ClientFactory):
    def __init__(self, id_zmq, data):
        self.id_zmq = id_zmq
        self.data = data
    def buildProtocol(self, addr):
        return EchoClient(self)
    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print ("Connection lost.")
        #reactor.stop()


class ZMQ_API_block():
    def __init__(self):

        reactor.callLater(0.3, self.TCPConnect)
        d = threads.deferToThread(self.read_write)

    def read_write(self):
        t = time.time()
        i = 0
        while True:
            try:
                sockets = dict(poll.poll())
                if frontend in sockets:
                    if sockets[frontend] == zmq.POLLIN:
                        [zmq_id0, zmq_id, data] = frontend.recv_multipart()
                        data = handler.f_f('z.P', data)
                        if zmq_id:
                            if zmq_id in conn:
                                data = handler.f_f('ztC', data)
                                if conn.get(zmq_id): conn[zmq_id].TCPSend(data)
                            else:
                                z_id, ip_out, port_out = (re.findall(b'0x[\d\w]*', zmq_id)[0],
                                    b'.'.join(re.findall(b'(?<=[,.])\d+', zmq_id)).decode('latin-1'),
                                    int(re.findall(b'(?<=:)\d+', zmq_id)[0]))
                                print(z_id, ip_out, port_out)
                                q_conn.put((zmq_id, data, ip_out, port_out,))
                                print('connectTCP')

                if time.time() - 1 > t:
                    t += 1
                    print('send / s = ', end= '')
                    print(i)
                    i = 0

                if backend in sockets:
                    if sockets[backend] == zmq.POLLIN:
                        i += 1
                        zmq_id, data, = backend.recv_multipart()
                        data = handler.f_f('z.R', data)
                        frontend.send_multipart([b'0', zmq_id, data])
            except zmq.core.error.ZMQError as e:
                print(e)
                break


    def TCPConnect(self):
        if not q_conn.empty():
            zmq_id, data, ip_out, port_out = q_conn.get()
            reactor.connectTCP(ip_out, port_out, EchoFactory(zmq_id, data))
        reactor.callLater(0.3, self.TCPConnect)
        return 0

context = zmq.Context()
frontend = context.socket(zmq.ROUTER)
frontend.bind(zmq_in)

backend = context.socket(zmq.ROUTER) # every connect will create dealer
backend.bind(zbackend)

poll = zmq.Poller()
poll.register(frontend, zmq.POLLIN)
poll.register(backend, zmq.POLLIN)

def signal_handler(signum, frame):
    print('interrupted')
    print('reactor stop')
    reactor.stop()
    print ('zmq close()')
    frontend.close()
    backend.close()


signal.signal(signal.SIGINT, signal_handler)


W = ZMQ_API_block()

reactor.run()

