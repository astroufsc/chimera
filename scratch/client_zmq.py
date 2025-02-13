# server.py
# a zeromq based server using the worker concept
import zmq
import time


def hello(host="127.0.0.1", port=9876):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://%s:%s" % (host, port))

    t0 = time.time()
    for i in range(10_000):
        socket.send(b"Hello")
        message = socket.recv()
        # print("Received reply: %s" % message)
    print("RPS: %.3f" % (10_000.0 / ((time.time() - t0))))


hello()
