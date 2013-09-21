import zmq
import threading
import time
import datetime
from random import choice
import signal


import argparse
parser = argparse.ArgumentParser(description=' zmq(port) -> zmq(port) ')
parser.add_argument("--lp", dest='localport', type=int, required=True,
                   help='local port')
parser.add_argument("--rp", dest='remoteport', type=int, required=True,
                   help='remote port')

args = parser.parse_args()


#z_port_in = 'tcp://*:15060'
z_port_in = "tcp://*:" + str(args.localport)
#z_port_out = 'tcp://*:15050'
z_port_out = "tcp://*:" + str(args.remoteport)

interrupted = False

def now():
    return datetime.datetime.now()

class handler():
    def __init__(self):
        pass
    def f_f(self, arg):
        #print(arg)
        zmq_id0, zmq_id, msg = arg[0], arg[1], arg[2]
        #msg = msg.replace(b"Hello", zmq_id)
        msg = ('%s  +/ 1: %s /' % (msg.decode('latin-1'), now())).encode('latin-1')
        return zmq_id0, zmq_id, msg
    def f_b(self, arg):
        #print(arg)
        zmq_id, msg = arg[0], arg[1]
        #msg = msg.replace(b"Hello", zmq_id)
        msg = ('%s -/ 1:  %s /' % (msg.decode('latin-1'), now())).encode('latin-1')
        return zmq_id, msg


class ServerTask():#(threading.Thread):
    """ServerTask"""
    def __init__(self):
        pass#threading.Thread.__init__ (self)

    def run(self):
        while True:
            try:
                sockets = dict(poll.poll())
                if interrupted:
                    print ("W: interrupt received, killing server...")
                    break
                if frontend in sockets:
                    if sockets[frontend] == zmq.POLLIN:
                        [zmq_id0, _id, msg] = H.f_f(frontend.recv_multipart())
                        #print ('Server received %s id %s\n' % (msg, _id))
                        backend.send(_id, zmq.SNDMORE)
                        backend.send(msg)
                if backend in sockets:
                    if sockets[backend] == zmq.POLLIN:
                        [_id, msg] = H.f_b(backend.recv_multipart())
                        #print ('Sending to frontend %s id %s\n' % (msg, _id))
                        frontend.send(b'0', zmq.SNDMORE)
                        frontend.send(_id, zmq.SNDMORE)
                        frontend.send(msg)
            except zmq.core.error.ZMQError as e:
                print(e)
                break
        print ('zmq close')
        frontend.close()
        backend.close()
        return 0

context = zmq.Context()
frontend = context.socket(zmq.ROUTER)
frontend.bind(z_port_in)

backend = context.socket(zmq.DEALER)
backend.setsockopt(zmq.IDENTITY, b'0')
backend.connect(z_port_out)

H = handler()

poll = zmq.Poller()
poll.register(frontend, zmq.POLLIN)
poll.register(backend,  zmq.POLLIN)

def signal_handler(signum, frame):
    print('interrupted')
    global interrupted
    interrupted = True
    #frontend.close()
    #backend.close()

def main():
    """main function"""
    signal.signal(signal.SIGINT, signal_handler)
    server = ServerTask()
    server.run()
    #server = ServerTask()
    #server.start()
    #server.join()

if __name__ == "__main__":
    main()
