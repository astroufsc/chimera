import random
import threading

import pytest

from chimera.core.bus import Bus
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.core.manager import Manager


class Raiser(ChimeraObject):
    def plain_boom(self):
        raise ValueError("plain boom")

    @lock
    def locked_boom(self):
        raise ValueError("locked boom")


@pytest.fixture
def manager():
    bus = Bus(f"tcp://127.0.0.1:{random.randint(20000, 60000)}")
    t = threading.Thread(target=bus.run_forever, daemon=True)
    t.start()
    assert bus._bus_started.wait(5)
    m = Manager(bus)
    yield m
    m.shutdown()
    bus.shutdown()
    t.join(timeout=10)


def test_locked_method_exception_reaches_caller(manager):
    assert manager.add_class(Raiser, "r", start=True)
    proxy = manager.get_proxy("/Raiser/r")
    proxy.__timeout__ = 5.0  # never hang the suite; a wedge fails via timeout
    with pytest.raises(Exception) as ei:
        proxy.locked_boom()
    assert "locked boom" in str(ei.value)


def test_plain_method_exception_reaches_caller(manager):
    assert manager.add_class(Raiser, "r", start=True)
    proxy = manager.get_proxy("/Raiser/r")
    proxy.__timeout__ = 5.0
    with pytest.raises(Exception) as ei:
        proxy.plain_boom()
    assert "plain boom" in str(ei.value)
