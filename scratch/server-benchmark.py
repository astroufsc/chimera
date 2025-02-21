import queue
import selectors
import threading
import time
import concurrent.futures
import pynng

q = queue.SimpleQueue()


def server(host: str, port: int):

    sk = pynng.Rep0()
    sk.listen(f"tcp://{host}:{port}")

    # ctx = sk.new_context()
    pool = concurrent.futures.ThreadPoolExecutor()

    selector = selectors.DefaultSelector()
    selector.register(sk.recv_fd, selectors.EVENT_READ)

    t0 = time.perf_counter_ns()
    n = 0

    try:
        while True:
            events = selector.select()
            for _ in events:
                msg = sk.recv(block=False)
                n += 1
                pool.submit(worker, sk, msg)

        # while not q.empty():
        #     ctx.send(q.get())
    except KeyboardInterrupt:
        sk.close()

    t1 = time.perf_counter_ns()
    print(f"Total time: {(t1 - t0) / 1e9:.2f} s")
    print(f"Total messages: {n}")
    print(f"Messages per second: {n / ((t1 - t0) / 1e9):.2f}")
    print(f"Average time per message: {(t1 - t0) / n:.2f} ns")


def worker(sk: pynng.Socket, msg: bytes):
    # ctx = sk.new_context()
    # me = threading.get_native_id()
    n = float(msg.decode())
    # print(f"[worker {me}] {time.perf_counter_ns()}: {n}")
    if n > 0:
        time.sleep(n)
    # q.put(msg)
    sk.send(msg)
    # ctx.send(msg)


if __name__ == "__main__":
    server("127.0.0.1", 5555)
