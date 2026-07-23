import random
import threading
import time

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


@pytest.fixture
def manager():
    bus = Bus(f"tcp://127.0.0.1:{random.randint(20000, 60000)}")
    bus_thread = threading.Thread(
        target=bus.run_forever, name="test-manager-bus", daemon=True
    )
    bus_thread.start()
    assert bus._bus_started.wait(5)

    manager = Manager(bus)

    yield manager

    manager.shutdown()
    bus.shutdown()
    bus_thread.join(timeout=10)
