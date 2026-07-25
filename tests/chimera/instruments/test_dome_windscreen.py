# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import inspect
import socket
import threading
import time

import pytest

from chimera.core.bus import Bus
from chimera.core.manager import Manager
from chimera.instruments.fakedome import FakeDome
from chimera.interfaces.dome import (
    DomeStatus,
    DomeWindScreen,
    InvalidDomePositionException,
    Mode,
)

METHODS = ["move_screen", "get_screen", "is_screen_moving", "abort_screen"]
EVENTS = ["screen_begin", "screen_complete"]


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
def dome(manager):
    return manager.add_class(FakeDome, "dome", {"telescope": "/FakeTelescope/0"})


@pytest.mark.parametrize("name", METHODS)
def test_signature_matches_the_interface(name):
    # plugins are written against these signatures; drifting them silently
    # breaks every out-of-tree implementation
    assert inspect.signature(getattr(FakeDome, name)) == inspect.signature(
        getattr(DomeWindScreen, name)
    )


@pytest.mark.parametrize("name", METHODS + EVENTS)
def test_reference_implementation_is_complete(name):
    assert callable(getattr(FakeDome(), name))


def test_features_reports_the_wind_screen():
    assert FakeDome().features("DomeWindScreen")


def test_config_keys_resolve():
    dome = FakeDome()
    for key in DomeWindScreen.__config__:
        dome[key]


def test_move_screen(dome):
    dome.move_screen(45.0)
    assert dome.get_screen() == 45.0
    assert not dome.is_screen_moving()

    dome.move_screen(10.0)
    assert dome.get_screen() == 10.0


def test_move_screen_outside_limits():
    # direct instance: the bus re-raises remote errors as plain Exception,
    # which would hide the exception type this asserts on
    dome = FakeDome()

    with pytest.raises(InvalidDomePositionException):
        dome.move_screen(dome["screen_max_alt"] + 1)

    with pytest.raises(InvalidDomePositionException):
        dome.move_screen(dome["screen_min_alt"] - 1)


def test_abort_screen(dome):
    completed = []
    dome.screen_complete += lambda alt, status: completed.append((alt, status))

    mover = threading.Thread(target=dome.move_screen, args=(90.0,))
    mover.start()

    while not dome.is_screen_moving():
        time.sleep(0.05)

    dome.abort_screen()
    mover.join(timeout=10)

    assert not dome.is_screen_moving()
    assert 0.0 < dome.get_screen() < 90.0

    # events are delivered asynchronously over the bus
    deadline = time.time() + 10.0
    while not completed and time.time() < deadline:
        time.sleep(0.05)
    assert completed[0] == (dome.get_screen(), DomeStatus.ABORTED)


def test_screen_events(dome):
    begun, completed = [], []
    dome.screen_begin += begun.append
    dome.screen_complete += lambda alt, status: completed.append((alt, status))

    dome.move_screen(30.0)

    deadline = time.time() + 10.0
    while not (begun and completed) and time.time() < deadline:
        time.sleep(0.05)

    assert begun == [0.0]  # altitude when the movement started
    assert completed == [(30.0, DomeStatus.OK)]


def test_tracking_follows_the_telescope_altitude(dome):
    dome["screen_offset"] = 5.0
    assert dome._screen_target(40.0) == 45.0

    # never asks for a position outside the screen travel
    assert dome._screen_target(89.0) == dome["screen_max_alt"]
    assert dome._screen_target(-10.0) == dome["screen_min_alt"]


def test_tracking_respects_the_resolution_deadband(dome):
    dome["screen_alt_resolution"] = 10.0
    dome.move_screen(40.0)

    dome._move_screen_if_needed(45.0)
    assert dome.get_screen() == 40.0  # within the deadband, no move

    dome._move_screen_if_needed(55.0)
    assert dome.get_screen() == 55.0


def test_tracking_can_be_turned_off(dome):
    dome["screen_track"] = False
    dome._move_screen_if_needed(45.0)
    assert dome.get_screen() == 0.0


def test_control_loop_tracks_the_telescope(manager):
    from chimera.core.site import Site
    from chimera.instruments.faketelescope import FakeTelescope

    manager.add_class(
        Site,
        "ufsc",
        {
            "name": "UFSC",
            "latitude": "-27 36 13",
            "longitude": "-48 31 20",
            "altitude": "20",
        },
    )
    telescope = manager.add_class(FakeTelescope, "fake")
    dome = manager.add_class(FakeDome, "dome", {"telescope": "/FakeTelescope/fake"})
    dome["screen_offset"] = 3.0

    dome.track()
    assert dome.get_mode() == Mode.Track

    dome.control()
    assert dome.get_screen() == telescope.get_alt() + 3.0


def test_metadata_carries_the_screen_altitude(dome):
    dome.move_screen(35.0)
    metadata = dict((key, value) for key, value, _ in dome.get_metadata({}))
    assert metadata["DOME_WSC"] == "35.00"
