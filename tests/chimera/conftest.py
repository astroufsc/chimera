import socket
from concurrent.futures import ThreadPoolExecutor

import pytest

from chimera.core.bus import Bus
from chimera.core.manager import Manager


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
    bus_loop.result()
    pool.shutdown()
