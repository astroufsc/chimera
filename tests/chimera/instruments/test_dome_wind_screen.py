# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import inspect
import socket
import threading
import time

import pytest

from chimera.core.bus import Bus
from chimera.core.manager import Manager
from chimera.instruments.dome import DomeBase
from chimera.instruments.fakedome import FakeDome
from chimera.interfaces.dome import (
    DomeStatus,
    DomeWindScreen,
    InvalidDomePositionException,
    Mode,
)

METHODS = [
    "move_wind_screen",
    "get_wind_screen_alt",
    "is_wind_screen_moving",
    "abort_wind_screen_move",
]
EVENTS = ["wind_screen_move_begin", "wind_screen_move_complete"]


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


def test_features_reports_the_optional_parts():
    dome = FakeDome()
    assert dome.features("DomeWindScreen")
    assert dome.features("DomeFlap")
    assert not DomeBase().features("DomeFlap")


def test_config_keys_resolve():
    dome = FakeDome()
    for key in DomeWindScreen.__config__:
        dome[key]


def test_move_wind_screen(dome):
    dome.move_wind_screen(45.0)
    assert dome.get_wind_screen_alt() == 45.0
    assert not dome.is_wind_screen_moving()

    dome.move_wind_screen(10.0)
    assert dome.get_wind_screen_alt() == 10.0


def test_move_wind_screen_outside_limits():
    # direct instance: the bus re-raises remote errors as plain Exception,
    # which would hide the exception type this asserts on
    dome = FakeDome()

    with pytest.raises(InvalidDomePositionException):
        dome.move_wind_screen(dome["wind_screen_max_alt"] + 1)

    with pytest.raises(InvalidDomePositionException):
        dome.move_wind_screen(dome["wind_screen_min_alt"] - 1)


def test_abort_wind_screen_move(dome):
    completed = []
    dome.wind_screen_move_complete += lambda alt, status: completed.append(
        (alt, status)
    )

    mover = threading.Thread(target=dome.move_wind_screen, args=(90.0,))
    mover.start()

    while not dome.is_wind_screen_moving():
        time.sleep(0.05)

    dome.abort_wind_screen_move()
    mover.join(timeout=10)

    assert not dome.is_wind_screen_moving()
    assert 0.0 < dome.get_wind_screen_alt() < 90.0

    # events are delivered asynchronously over the bus
    deadline = time.time() + 10.0
    while not completed and time.time() < deadline:
        time.sleep(0.05)
    assert completed[0] == (dome.get_wind_screen_alt(), DomeStatus.ABORTED)


def test_screen_events(dome):
    begun, completed = [], []
    dome.wind_screen_move_begin += begun.append
    dome.wind_screen_move_complete += lambda alt, status: completed.append(
        (alt, status)
    )

    dome.move_wind_screen(30.0)

    deadline = time.time() + 10.0
    while not (begun and completed) and time.time() < deadline:
        time.sleep(0.05)

    assert begun == [0.0]  # altitude when the movement started
    assert completed == [(30.0, DomeStatus.OK)]


def test_tracking_follows_the_telescope_altitude(dome):
    dome["wind_screen_offset"] = 5.0
    assert dome._wind_screen_target(40.0) == 45.0

    # never asks for a position outside the screen travel
    assert dome._wind_screen_target(89.0) == dome["wind_screen_max_alt"]
    assert dome._wind_screen_target(-10.0) == dome["wind_screen_min_alt"]


def test_tracking_respects_the_resolution_deadband(dome):
    dome["wind_screen_alt_resolution"] = 10.0
    dome.move_wind_screen(40.0)

    dome._move_wind_screen_if_needed(45.0)
    assert dome.get_wind_screen_alt() == 40.0  # within the deadband, no move

    dome._move_wind_screen_if_needed(55.0)
    assert dome.get_wind_screen_alt() == 55.0


def test_tracking_can_be_turned_off(dome):
    dome["wind_screen_track"] = False
    dome._move_wind_screen_if_needed(45.0)
    assert dome.get_wind_screen_alt() == 0.0


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
    dome["wind_screen_offset"] = 3.0

    dome.track()
    assert dome.get_mode() == Mode.Track

    dome.control()
    assert dome.get_wind_screen_alt() == telescope.get_alt() + 3.0


def test_metadata_carries_the_wind_screen_altitude(dome):
    dome.move_wind_screen(35.0)
    metadata = dict((key, value) for key, value, _ in dome.get_metadata({}))
    assert metadata["DOME_WSC"] == "35.00"


def test_metadata_carries_the_flap_status(dome):
    metadata = dict((key, value) for key, value, _ in dome.get_metadata({}))
    assert metadata["DOME_FLP"] == "Closed"

    dome.open_slit()
    dome.open_flap()

    metadata = dict((key, value) for key, value, _ in dome.get_metadata({}))
    assert metadata["DOME_FLP"] == "Open"


def test_metadata_skips_the_flap_when_the_driver_has_none():
    # DomeBase no longer claims DomeFlap: drivers with a flap mix it in
    class SlitOnlyDome(DomeBase):
        def is_slit_open(self):
            return False

    metadata = dict((key, value) for key, value, _ in SlitOnlyDome().get_metadata({}))
    assert "DOME_FLP" not in metadata
    assert "DOME_SLT" in metadata
