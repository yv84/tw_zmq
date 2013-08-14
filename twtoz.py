import time
import datetime
import zmq
import re
import signal

from twisted.internet import reactor, protocol, threads


#argparse
import argparse
parser = argparse.ArgumentParser(description=' tcp/ip(port) -> zmq(port) -> tcp/ip(ip/port) ')
parser.add_argument("--lp", dest='localport', type=int, required=True,
                   help='local port')
parser.add_argument("--zp", dest='zmqport', type=int, required=True,
                   help='remote zmq port')
parser.add_argument("--rip", dest='remoteip', type=str, required=True,
                   help='remote ip')
parser.add_argument("--rp", dest='remoteport', type=int, required=True,
                   help='remote port')

args = parser.parse_args()

#port_in = {15001: (b'127.0.0.1', b'15011')}
print(args)
port_in = {args.localport: ( (args.remoteip).encode('latin-1'), (str(args.remoteport)).encode('latin-1') )}
#port_zmq = "tcp://*:15060"
port_zmq = "tcp://*:" + str(args.zmqport)
zs_port = "inproc://ps"

conn = {}

#profile handler
def now():                               # текущее время на сервере
    return datetime.datetime.now()

class handler():
    def __init__(self):
        pass
    def f_f(name, data):
        return ('%s  +/ %s: %s /' % (data.decode('latin-1'), name, now())).encode('latin-1')
    def f_f(name, data):
        return ('%s  -/ %s: %s /' % (data.decode('latin-1'), name, now())).encode('latin-1')


from twisted.internet import protocol, reactor
class Echo(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.d = b''
        self.data = b''

    def connectionMade(self):
        self.id_zmq = b''.join([b'+', re.findall(
                    b'0x[\d\w]*', 
                    self.__str__().encode('latin-1'))[0],
                    b',', self.factory.ip_out, 
                    b':', self.factory.port_out])
        conn[self.id_zmq] = self
        print('conn = ', end='')
        print(conn)
        print('self.id_zmq  = ', end = '')
        print(self.id_zmq)
        self.frontend = context.socket(zmq.DEALER) #kajdnoe podlyuchenie zoxdast dealera
        self.frontend.setsockopt(zmq.IDENTITY, self.id_zmq)
        self.frontend.connect(zs_port)
        self.closeTimer  = time.time()
        reactor.callLater(3, self.isClose)
        self.isCl = False

    def dataReceived(self, data):
        self.closeTimer = time.time()
        self.frontend.send_multipart([data])

    def TCPSend(self, data):
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
    def __init__(self, p_in):
        self.ip_out = p_in[0]
        self.port_out = p_in[1]
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

class ZMQ_API_block():
    def __init__(self):
        d = threads.deferToThread(self.read_write)

    def read_write(self):
        t = time.time()
        i = 0
        while True:
            try:
                sockets = dict(poll.poll())
                if backend in sockets:
                    if sockets[backend] == zmq.POLLIN:
                        [zmq_id, data] = backend.recv_multipart()
                        data = handler.f_f('z.P', data)
                        #print(zmq_id)
                        #print(data)
                        #print(conn)
                        if conn.get(zmq_id): conn[zmq_id].TCPSend(data)
                if time.time() - 1 > t:
                    t += 1
                    print('send / s = ', end= '')
                    print(i)
                    i = 0
                if frontend in sockets:
                    if sockets[frontend] == zmq.POLLIN:
                        i += 1
                        zmq_id, data = frontend.recv_multipart()
                        #print('frontend_recv = ',end ='') 
                        #print(zmq_id, data)
                        backend.send_multipart([zmq_id, data])
            except zmq.core.error.ZMQError as e:
                print(e)
                break



context = zmq.Context()
backend = context.socket(zmq.DEALER)
backend.setsockopt(zmq.IDENTITY, b'0')
backend.connect(port_zmq)

frontend = context.socket(zmq.ROUTER) #kajdnoe podlyuchenie zoxdast dealera
frontend.bind(zs_port)

def signal_handler(signum, frame):
    print('interrupted')
    print('reactor stop')
    reactor.stop()
    print ('zmq close()')
    frontend.close()
    backend.close()


signal.signal(signal.SIGINT, signal_handler)


poll = zmq.Poller()
poll.register(backend, zmq.POLLIN)
poll.register(frontend, zmq.POLLIN)


W = ZMQ_API_block()


for p_in in port_in.items():
    reactor.listenTCP(p_in[0], EchoFactory(p_in[1]))
reactor.run()

