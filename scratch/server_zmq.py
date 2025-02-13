# server.py
# a zeromq based server using the worker concept
import zmq
import concurrent.futures
import time


def worker(ctx):
    socket = ctx.socket(zmq.REP)
    socket.connect("inproc://workers")

    while True:
        message = socket.recv()
        # print("Received request: {}".format(message))
        socket.send(b"World")


def serve(host="127.0.0.1", port=9876):
    ctx = zmq.Context().instance()
    socket = ctx.socket(zmq.ROUTER)
    socket.bind("tcp://{}:{}".format(host, port))
    print("Server started at tcp://{}:{}".format(host, port))

    dealer = ctx.socket(zmq.DEALER)
    dealer.bind("inproc://workers")
    print("Worker started at inproc://workers")

    pool = concurrent.futures.ThreadPoolExecutor(8)
    for _ in range(5):
        pool.submit(worker, ctx)

    zmq.proxy(socket, dealer)
    pool.shutdown(wait=True)


serve()
