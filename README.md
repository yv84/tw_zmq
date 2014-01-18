<pre>
twtoz.py : twisted -> pyzmq
zasync.py : pyzmq -> pyzmq  (based on zguide/examples/Python/asyncsrv.py)
ztotw.py : pyzmq -> twisted
twproxy.py : twisted -> twisted

tcp/ip --> |                               | --> tcp/ip
  ...      | tw-zmq -> zasync -> zmq-tw    |       ...
tcp/ip --> |                               | --> tcp/ip




requirement:
         python3
         py_zmq: zmq.zmq_version();>>>2.1.11
         Version('twisted', 13, 1, 0) 
testing:
         $ python3 -m unittest -v testing.test1
         $ python3 -m unittest -v testing.testtwproxy

</pre>
