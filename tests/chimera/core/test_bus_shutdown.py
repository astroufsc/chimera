import os
import signal
import time
from concurrent.futures.thread import ThreadPoolExecutor

from chimera.core.bus import Bus


def test_bus_graceful_shutdown():
    bus = Bus("tcp://127.0.0.1:47854")

    print("")

    def recv_message():
        # simulate a pending request, a Proxy is trying to pop an answer while the bus is shutting down
        print("recv: receiving message")
        msg = bus._pop()
        assert msg is None, "bus.pop() should return None only when the bus is exiting"

    def ask_for_shutdown():
        print("shutdown: will wait 1.0s and ask for shutdown")
        time.sleep(1.0)
        bus.shutdown()
        print("shutdown: request sent")

    pool = ThreadPoolExecutor()
    recv_future = pool.submit(recv_message)
    shutdown_future = pool.submit(ask_for_shutdown)

    bus.run_forever()

    recv_future.result()
    shutdown_future.result()

    pool.shutdown()

    assert bus.is_dead(), "bus is still alive?"

    assert all([th.is_alive() is False for th in bus._pool._threads]), (
        "some bus threads are still alive?"
    )


def test_bus_ctrl_c_shutdown():
    bus = Bus("tcp://127.0.0.1:47854")

    print("")

    def recv_message():
        # simulate a pending request, a Proxy is trying to pop an answer while the bus is shutting down
        print("recv: receiving message")
        msg = bus._pop()
        assert msg is None, "bus.pop() should return None only when the bus is exiting"

    def force_shutdown():
        print("shutdown: send a SIGINT to our process to simulate ctrl-c")
        time.sleep(1.0)
        os.kill(os.getpid(), signal.SIGINT)
        print("shutdown: request sent")

    pool = ThreadPoolExecutor()
    recv_future = pool.submit(recv_message)
    shutdown_future = pool.submit(force_shutdown)

    bus.run_forever()

    recv_future.result()
    shutdown_future.result()

    pool.shutdown()

    assert bus.is_dead(), "bus is still alive?"

    assert all([th.is_alive() is False for th in bus._pool._threads]), (
        "some bus threads are still alive?"
    )
