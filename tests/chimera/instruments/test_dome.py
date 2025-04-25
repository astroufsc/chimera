# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import time
import random
import threading
import logging

from chimera.core.manager import Manager
from chimera.core.site import Site

from chimera.util.coord import Coord
from chimera.util.position import Position

from chimera.interfaces.dome import InvalidDomePositionException, DomeStatus

from .base import FakeHardwareTest, RealHardwareTest

import chimera.core.log
import pytest

chimera.core.log.set_console_level(int(1e10))
log = logging.getLogger("chimera.tests")

# hack for event triggering asserts
fired_events = {}


def assert_dome_az(dome_az, other_az, eps):
    assert (
        abs(dome_az - other_az) <= eps
    ), f"dome az={dome_az} other az={other_az} (eps={eps})"


class DomeTest(object):

    dome = ""
    telescope = ""
    manager = None

    def assert_events(self, slew_status=None, sync=False):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        if slew_status:
            assert "slew_begin" in fired_events
            assert isinstance(fired_events["slew_begin"][1], Coord)

            assert "slew_complete" in fired_events
            assert fired_events["slew_complete"][0] > fired_events["slew_begin"][0]
            assert isinstance(fired_events["slew_complete"][1], Coord)
            assert fired_events["slew_complete"][2] in DomeStatus
            assert fired_events["slew_complete"][2] == slew_status

        if sync:
            assert "sync_begin" in fired_events
            assert "sync_complete" in fired_events
            assert fired_events["sync_complete"][0] > fired_events["sync_begin"][0]

    def setup_events(self):

        def slew_begin_clbk(position):
            fired_events["slew_begin"] = (time.time(), position)

        def slew_complete_clbk(position, status):
            fired_events["slew_complete"] = (time.time(), position, status)

        def sync_begin_clbk():
            fired_events["sync_begin"] = (time.time(),)

        def sync_complete_clbk():
            fired_events["sync_complete"] = (time.time(),)

        dome = self.manager.get_proxy(self.dome)
        dome.slew_begin += slew_begin_clbk
        dome.slew_complete += slew_complete_clbk
        dome.sync_begin += sync_begin_clbk
        dome.sync_complete += sync_complete_clbk

    def test_stress_dome_track(self):

        dome = self.manager.get_proxy(self.dome)
        tel = self.manager.get_proxy(self.telescope)

        dome.track()

        for i in range(10):

            self.setup_events()

            ra = f"{random.randint(7, 15)} {random.randint(0, 59)} 00"
            dec = f"{random.randint(-90, 0)} {random.randint(0, 59)} 00"
            tel.slew_to_ra_dec(Position.from_ra_dec(ra, dec))

            dome.sync_with_tel()
            assert_dome_az(dome.get_az(), tel.get_az(), dome["az_resolution"])
            self.assert_events(sync=True)

            time.sleep(random.randint(0, 10))

    pytest.mark.skip(reason="just for visual testing")

    def test_stress_dome_slew(self):
        dome = self.manager.get_proxy(self.dome)

        quit = threading.Event()

        def get_az_stress():
            while not quit.is_set():
                dome.get_az()
                time.sleep(0.5)

        az_thread = threading.Thread(target=get_az_stress)
        az_thread.start()

        for i in range(10):
            az = random.randint(0, 359)
            dome.slew_to_az(Coord.from_d(az))
            time.sleep(5)

        quit.set()
        az_thread.join()

    def test_get_az(self):
        dome = self.manager.get_proxy(self.dome)
        assert dome.get_az() >= 0

    def test_slew_to_az(self):

        dome = self.manager.get_proxy(self.dome)

        start = dome.get_az()
        delta = 20

        dome.slew_to_az(start + delta)

        assert_dome_az(dome.get_az(), (start + delta), dome["az_resolution"])

        with pytest.raises(InvalidDomePositionException):
            dome.slew_to_az(9999)

        # event check
        self.assert_events(DomeStatus.OK)

    def test_slit(self):

        dome = self.manager.get_proxy(self.dome)

        dome.open_slit()
        assert dome.is_slit_open() is True

        dome.close_slit()
        assert dome.is_slit_open() is False


#
# setup real and fake tests
#
class TestFakeDome(FakeHardwareTest, DomeTest):

    def setup(self):

        self.manager = Manager()

        self.manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13 ",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

        from chimera.instruments.faketelescope import FakeTelescope
        from chimera.instruments.fakedome import FakeDome

        self.manager.add_class(FakeTelescope, "fake")
        self.manager.add_class(
            FakeDome, "dome", {"telescope": "/FakeTelescope/0", "mode": "Track"}
        )
        self.telescope = "/FakeTelescope/0"
        self.dome = "/FakeDome/0"

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()


class TestRealDome(RealHardwareTest, DomeTest):

    def setup(self):

        self.manager = Manager()

        self.manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13 ",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

        from chimera.instruments.domelna40cm import DomeLNA40cm
        from chimera.instruments.meade import Meade

        self.manager.add_class(Meade, "meade", {"device": "/dev/ttyS6"})
        self.manager.add_class(
            DomeLNA40cm,
            "lna40",
            {"device": "/dev/ttyS9", "telescope": "/Meade/0", "mode": "Stand"},
        )

        self.telescope = "/Meade/meade"
        self.dome = "/DomeLNA40cm/0"

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()
