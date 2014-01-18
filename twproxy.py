import argparse


from twisted.internet import protocol, reactor


def agrparser():
    parser = argparse.ArgumentParser(
        description=' proxy ')
    parser.add_argument("--port_in", dest='port_in',
        type=str, required=True, help='local port')
    parser.add_argument("--ip_out", dest='ip_out',
        type=str, required=True, help='remote ip')
    parser.add_argument("--port_out", dest='port_out',
        type=str, required=True, help='remote port')
    args = parser.parse_args()
    return args


# proxy server factory
class TwServer(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.factory.proxy.update({self: 
            {'g_c': self, 'g_s': None, 'data_g_s': b'', 'data_g_c': b''}})
        self.proxy = self.factory.proxy[self]

    def connectionMade(self):
        # create client Factory protocol
        reactor.connectTCP(self.factory.conn['tw_c']['ip'],
                int(self.factory.conn['tw_c']['port']),
                TwClientFactory(self, self.factory.proxy))
        reactor.callLater(0.01, self.send)
        print("proxy server connectionMade")

    def dataReceived(self, data):
        self.factory.proxy[self]['data_g_c'] = b''.join(
            [self.factory.proxy[self]['data_g_c'], data])

    def send(self):
        if self.factory.proxy[self]['data_g_s']:
            data, self.factory.proxy[self]['data_g_s'] = \
                self.factory.proxy[self]['data_g_s'], b''
            print(b''.join([b's->', data]))
            self.transport.write(data)
        reactor.callLater(0.01, self.send)
        return 

    def connectionLost(self, reason):
        print("proxy server connection lost.")
 

class TwServerFactory(protocol.Factory):
    def __init__(self, proxy, conn):
        self.proxy = proxy
        self.conn = conn

    def buildProtocol(self, addr):
        return TwServer(self)


# proxy client factory
class TwClient(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.factory.proxy[self.factory.server_transport]['g_s'] = self # {tw_s: tw_c}
        #print("\nproxy client init")

    def connectionMade(self):
        #print("proxy client connectionMade")
        reactor.callLater(0.01, self.send)
        #print(self.factory.proxy)

    def dataReceived(self, data):
        self.factory.proxy[self.factory.server_transport]['data_g_s'] = b''.join(
            [self.factory.proxy[self.factory.server_transport]['data_g_s'], data])

    def send(self):
        if self.factory.proxy[self.factory.server_transport]['data_g_c']:
            data, self.factory.proxy[self.factory.server_transport]['data_g_c'] = \
                self.factory.proxy[self.factory.server_transport]['data_g_c'], b''
            print(b''.join([b'c->', data]))
            self.transport.write(data)
        reactor.callLater(0.01, self.send)
        return 


class TwClientFactory(protocol.ClientFactory):
    def __init__(self, server_transport, proxy):
        self.server_transport = server_transport
        self.proxy = proxy

    def buildProtocol(self, addr):
        return TwClient(self)

    def clientConnectionFailed(self, connector, reason):
        print("proxy client connection failed.")

    def clientConnectionLost(self, connector, reason):
        print("proxy client connection lost.")



def main(args):
    proxy = {}
    conn = {
        'tw_s': {'ip':'0.0.0.0', 'port': args['port_in']},
        'tw_c': {'ip':args['ip_out'], 'port':args['port_out']},   
    }
    #print('reactor.listenTCP')
    reactor.listenTCP(int(conn['tw_s']['port']), TwServerFactory(proxy, conn))
    #print('reactor.run')
    reactor.run()

if __name__ == '__main__':
    print('start')
    args = agrparser()
    args = {'port_in': args.port_in, 'ip_out': args.ip_out, 'port_out': args.port_out, }
    main(args)
