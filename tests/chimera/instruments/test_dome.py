# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import logging
import random
import threading
import time

import pytest

import chimera.core.log
from chimera.core.site import Site
from chimera.instruments.fakedome import FakeDome
from chimera.instruments.faketelescope import FakeTelescope
from chimera.interfaces.dome import DomeStatus

chimera.core.log.set_console_level(int(1e10))
log = logging.getLogger("chimera.tests")

# hack for event triggering asserts
fired_events = {}


def slew_begin_clbk(position):
    fired_events["slew_begin"] = (time.time(), position)


def slew_complete_clbk(position, status):
    fired_events["slew_complete"] = (time.time(), position, status)


def sync_begin_clbk():
    fired_events["sync_begin"] = (time.time(),)


def sync_complete_clbk():
    fired_events["sync_complete"] = (time.time(),)


def assert_dome_az(dome_az, other_az, eps):
    assert abs(dome_az - other_az) <= eps, (
        f"dome az={dome_az} other az={other_az} (eps={eps})"
    )


@pytest.fixture
def dome(manager):
    manager.add_class(
        Site,
        "lna",
        {
            "name": "UFSC",
            "latitude": "-27 36 13 ",
            "longitude": "-48 31 20",
            "altitude": "20",
        },
    )

    manager.add_class(FakeTelescope, "fake")
    manager.add_class(
        FakeDome, "dome", {"telescope": "/FakeTelescope/0", "mode": "Track"}
    )

    fired_events.clear()

    dome = manager.get_proxy("/FakeDome/0")
    dome.slew_begin += slew_begin_clbk
    dome.slew_complete += slew_complete_clbk
    dome.sync_begin += sync_begin_clbk
    dome.sync_complete += sync_complete_clbk

    return dome


class TestFakeDome:
    def assert_events(self, slew_status=None, sync=False):
        # for every slew, we need to check if all events were fired in the
        # right order and with the right parameters

        # NOTE: no delivery-time ordering asserts: events are delivered
        # asynchronously and the bus does not guarantee cross-event callback
        # ordering

        if slew_status:
            assert "slew_begin" in fired_events
            assert isinstance(fired_events["slew_begin"][1], (int, float))

            assert "slew_complete" in fired_events
            assert isinstance(fired_events["slew_complete"][1], (int, float))
            assert fired_events["slew_complete"][2] in DomeStatus
            assert fired_events["slew_complete"][2] == slew_status

        if sync:
            assert "sync_begin" in fired_events
            assert "sync_complete" in fired_events

    @pytest.mark.skip(reason="stress test, for manual runs only")
    def test_stress_dome_track(self, dome, manager):
        tel = manager.get_proxy("/FakeTelescope/0")

        dome.track()

        for i in range(10):
            ra = random.randint(7, 15) + random.randint(0, 59) / 60.0
            dec = -random.randint(0, 90) + random.randint(0, 59) / 60.0
            tel.slew_to_ra_dec(ra, dec)

            dome.sync_with_tel()
            assert_dome_az(dome.get_az(), tel.get_az(), dome["az_resolution"])
            self.assert_events(sync=True)

            time.sleep(random.randint(0, 10))

    @pytest.mark.skip(reason="just for visual testing")
    def test_stress_dome_slew(self, dome):
        quit = threading.Event()

        def get_az_stress():
            while not quit.is_set():
                dome.get_az()
                time.sleep(0.5)

        az_thread = threading.Thread(target=get_az_stress)
        az_thread.start()

        for i in range(10):
            az = random.randint(0, 359)
            dome.slew_to_az(az)
            time.sleep(5)

        quit.set()
        az_thread.join()

    def test_get_az(self, dome):
        assert dome.get_az() >= 0

    def test_slew_to_az(self, dome, wait_for):
        start = dome.get_az()
        delta = 20

        dome.slew_to_az(start + delta)

        assert_dome_az(dome.get_az(), (start + delta), dome["az_resolution"])

        with pytest.raises(Exception, match="InvalidDomePositionException"):
            dome.slew_to_az(9999)

        # event check
        assert wait_for(lambda: "slew_complete" in fired_events)
        self.assert_events(DomeStatus.OK)

    def test_slit(self, dome):
        dome.open_slit()
        assert dome.is_slit_open() is True

        dome.close_slit()
        assert dome.is_slit_open() is False
