#! /usr/local/bin/python3

import datetime
import time
from twisted.internet import reactor, protocol

def now():
    return datetime.datetime.now()


class Echo(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols+1

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols-1

    def dataReceived(self, data):
        data = ('Echo disp hw=>%s at %s' % (str(data),
                        now())).encode('latin-1')
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    def __init__(self):
        self.numProtocols = 0
    def buildProtocol(self, addr):
        return Echo(self)
    def clientConnectionFailed(self, connector, reason):
        print ("Connection failed.")
        reactor.stop()
    def clientConnectionLost(self, connector, reason):
        print ("Connection lost.")
        reactor.stop()

def tcp_serv(conn):
    reactor.listenTCP(int(conn['port']), EchoFactory())
    reactor.run()


if __name__ == "__main__":
    conn = {'ip': '127.0.0.1', 'port': '15075'}
    reactor.listenTCP(int(conn['port']), EchoFactory())
    reactor.run()
