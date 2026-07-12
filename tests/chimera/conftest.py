import socket
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from chimera.core.bus import Bus
from chimera.core.manager import Manager


@pytest.fixture
def wait_for():
    """
    Poll a predicate until it is true or the timeout expires. Use this
    instead of fixed sleeps when waiting for asynchronous event delivery.
    """

    def waiter(predicate, timeout=10.0, interval=0.05):
        t0 = time.monotonic()
        while not predicate() and time.monotonic() - t0 < timeout:
            time.sleep(interval)
        return predicate()

    return waiter


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def manager():
    bus = Bus(f"tcp://127.0.0.1:{get_free_port()}")
    pool = ThreadPoolExecutor()
    bus_loop = pool.submit(bus.run_forever)

    manager = Manager(bus)

    yield manager

    manager.shutdown()
    bus.shutdown()
    # bounded wait: raise instead of hanging the whole session if the bus
    # loop fails to exit
    bus_loop.result(timeout=30)
    pool.shutdown(wait=False)
