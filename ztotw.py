import time
import re
import queue
import datetime
import signal
import argparse

import zmq
from twisted.internet import reactor, protocol, threads


def agrparser():
    parser = argparse.ArgumentParser(
        description=' zmq(port) -> tcp/ip(ip/port) ')
    parser.add_argument("--zp", dest='zmqport',
        type=int, required=True, help='local port')
    parser.add_argument("--rip", dest='remoteip',
        type=str, required=True, help='remote ip')
    parser.add_argument("--rp", dest='remoteport',
        type=int, required=True, help='remote port')
    args = parser.parse_args()
    return args




#ip_out = args.remoteip

#zmq_in = "tcp://*:" + str(args.localport)

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
        connection[self.factory.id_zmq] = self
        self.zsocket = context.socket(zmq.DEALER) # every connect will create dealer
        self.zsocket.setsockopt(zmq.IDENTITY, self.factory.id_zmq)
        self.zsocket.connect(zbackend)
        print(connection)
        self.tcpSend(self.factory.data)
        self.closeTimer  = time.time()
        reactor.callLater(3, self.isClose)
        self.isCl = False

    def dataReceived(self, data):
        self.closeTimer = time.time()
        data = Time.f_f('t.R', data)
        self.zsocket.send_multipart([data,])

        def tcpSend(self, data):
            if data == b'/x00':
                self.isCl = True
        data = Time.f_f('t.S', data)
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
        print('connection = ', end='')
        print(connection)
        print('self.id_zmq  = ', end = '')
        print(self.factory.id_zmq)
        connection.pop(self.factory.id_zmq)
        print('Connection close.')
        self.transport.loseConnection()
        print('connection = ', end='')
        print(connection)
        del self.factory
        del self

class EchoFactory(protocol.ClientFactory):
    def __init__(self, zmq_handler, id_zmq, data):
        self.zmq_handler = zmq_handler
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


class ZmqHandler():
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.context = zmq.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(self.conn['zc']['port'])

        # every connect will create dealer
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(ZS_PAIR_PORT)

        self.poll = zmq.Poller()
        self.poll.register(self.frontend, zmq.POLLIN)
        self.poll.register(self.backend, zmq.POLLIN)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print ('zmq close()')
        self.frontend.close()
        self.backend.close()



    def run(self):
        actor.callLater(0.3, self.tcpConnect)
        d = threads.deferToThread(self.read_write)



    def backend_handler(self):
        i += 1
        zmq_id, data, = self.backend.recv_multipart()
        data = Time.f_f('z.R', data)
        self.frontend.send_multipart([b'0', zmq_id, data])

    def frontend_handler(self):
        [zmq_id0, zmq_id, data] = self.frontend.recv_multipart()
        data = Time.f_f('z.P', data)
        if zmq_id:
            if zmq_id in connection:
                data = Time.f_f('ztC', data)
                if connection.get(zmq_id):
                     connection[zmq_id].tcpSend(data)
            else:
                # get conn['server'] from packet header -> zmq_id
                z_id, ip_out, port_out = (re.findall(b'0x[\d\w]*', zmq_id)[0],
                    b'.'.join(re.findall(b'(?<=[,.])\d+',zmq_id)).decode('latin-1'),
                    int(re.findall(b'(?<=:)\d+', zmq_id)[0]))
                print(z_id, ip_out, port_out)
                q_conn.put((zmq_id, data, ip_out, port_out,))
                print('connectTCP')


    def read_write(self):
        t = time.time()
        i = 0
        while True:
            try:
                sockets = dict(poll.poll())
                if frontend in sockets:
                    if sockets[frontend] == zmq.POLLIN:
                        self.frontend_handler()
                if time.time() - 1 > t:
                    t += 1
                    print('send / s = ', end= '')
                    print(i)
                    i = 0

                if backend in sockets:
                    if sockets[backend] == zmq.POLLIN:
                        self.backend_handler()
            except zmq.core.error.ZMQError as e:
                print(e)
                break


    def tcpConnect(self):
        if not q_conn.empty():
            zmq_id, data, ip_out, port_out = q_conn.get()
            reactor.connectTCP(ip_out, port_out,
                EchoFactory(self, zmq_id, data))
        reactor.callLater(0.3, self.tcpConnect)
        return 0


def signal_handler(signum, frame):
    print('interrupted')
    print('reactor stop')
    reactor.stop()
    print ('zmq close()')
    frontend.close()
    backend.close()


def main(conn):
    with ZmqHandler(conn) as zmq_handler:
        zma_handler.run()
        reactor.run()

def z_to_tw(conn):
    signal.signal(signal.SIGTERM, signal_handler)
    main(conn)


if __name__ == '__main__':

    args = agrparser()

    connzs = {'ip': '127.0.0.1', 'port': args.zmqport}
    connts = {'ip': args.remoteip, 'port': args.remoteport}
    conn = {}
    print('wait')
    for d, k in zip((connts, connzc), ('ts', 'zc')):
        conn[k] = d
        os.system('fuser -k '+d['port']+'/tcp')
    print(conn)
    print('start')
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    #signal.signal(signal.SIGQUIT, signal_handler)
    main(conn)
