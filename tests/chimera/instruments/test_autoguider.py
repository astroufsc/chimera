# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import inspect
import socket
import threading
import time

import pytest

from chimera.core.bus import Bus
from chimera.core.manager import Manager
from chimera.instruments.fakeautoguider import FakeAutoguider
from chimera.interfaces.autoguider import Autoguider, GuiderException, GuiderStatus

METHODS = [
    "start_guiding",
    "stop_guiding",
    "abort",
    "is_guiding",
    "get_status",
    "dither",
    "find_star",
]

EVENTS = [
    "offset_complete",
    "guide_start",
    "guide_stop",
    "star_acquired",
    "star_lost",
    "dither_complete",
]


def _free_tcp_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def manager():
    # local fixture on purpose: events need a live bus, and the shared one
    # in tests/chimera/conftest.py still uses the pre-bus Manager() API
    bus = Bus(f"tcp://127.0.0.1:{_free_tcp_port()}")
    bus_thread = threading.Thread(target=bus.run_forever, name="Bus", daemon=True)
    bus_thread.start()
    manager = Manager(bus=bus)
    yield manager
    manager.shutdown()
    bus.shutdown()
    bus_thread.join(timeout=10)


@pytest.fixture
def guider(manager):
    return manager.add_class(FakeAutoguider, "guider")


@pytest.mark.parametrize("name", METHODS)
def test_signature_matches_the_interface(name):
    # plugins are written against these signatures; drifting them silently
    # breaks every out-of-tree implementation
    assert inspect.signature(getattr(FakeAutoguider, name)) == inspect.signature(
        getattr(Autoguider, name)
    )


@pytest.mark.parametrize("name", METHODS + EVENTS)
def test_reference_implementation_is_complete(name):
    assert callable(getattr(FakeAutoguider(), name))


def test_config_keys_resolve():
    # the metaclass merges the interface __config__ into the plugin's
    guider = FakeAutoguider()
    for key in Autoguider.__config__:
        guider[key]


def test_guiding_lifecycle(guider):
    assert guider.get_status() == GuiderStatus.OFF
    assert not guider.is_guiding()

    position = guider.start_guiding()
    assert position == guider.find_star()
    assert guider.is_guiding()
    assert guider.get_status() == GuiderStatus.GUIDING

    guider.stop_guiding()
    assert not guider.is_guiding()
    assert guider.get_status() == GuiderStatus.OFF


def test_abort_reports_aborted(guider):
    guider.start_guiding()
    guider.abort()
    assert guider.get_status() == GuiderStatus.ABORTED
    assert not guider.is_guiding()


def test_dither_requires_guiding():
    # direct instance: the bus re-raises remote errors as plain Exception,
    # which would hide the exception type this asserts on
    with pytest.raises(GuiderException):
        FakeAutoguider().dither()


def test_dither_moves_the_lock_position(guider):
    guider.start_guiding()
    before = list(guider.find_star())

    guider.dither(amount=5.0, ra_only=True)
    after = guider.find_star()
    assert after[0] == before[0] + 5.0
    assert after[1] == before[1]  # ra_only leaves the other axis alone

    guider.dither(amount=5.0, ra_only=False)
    assert guider.find_star()[1] == before[1] + 5.0


def test_offsets_are_published_only_while_guiding(guider):
    offsets = []
    guider.offset_complete += offsets.append

    guider.control()
    assert offsets == []  # not guiding yet

    guider.start_guiding()
    guider.control()

    # events are delivered asynchronously over the bus
    deadline = time.time() + 10.0
    while not offsets and time.time() < deadline:
        time.sleep(0.05)
    assert len(offsets) == 1

    # the payload the interface documents and chimera-guider --monitor reads
    assert set(offsets[0]) == {
        "frame",
        "dx",
        "dy",
        "ra_distance",
        "dec_distance",
        "snr",
    }
