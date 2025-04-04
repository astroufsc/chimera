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

chimera.core.log.setConsoleLevel(int(1e10))
log = logging.getLogger("chimera.tests")

# hack for event  triggering asserts
FiredEvents = {}


def assertDomeAz(domeAz, otherAz, eps):
    assert (
        abs(domeAz - otherAz) <= eps
    ), f"dome az={domeAz} other az={otherAz} (eps={eps})"


class DomeTest(object):

    DOME = ""
    TELESCOPE = ""
    manager = None

    def assertEvents(self, slewStatus=None, sync=False):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        if slewStatus:
            assert "slewBegin" in FiredEvents
            assert isinstance(FiredEvents["slewBegin"][1], Coord)

            assert "slewComplete" in FiredEvents
            assert FiredEvents["slewComplete"][0] > FiredEvents["slewBegin"][0]
            assert isinstance(FiredEvents["slewComplete"][1], Coord)
            assert FiredEvents["slewComplete"][2] in DomeStatus
            assert FiredEvents["slewComplete"][2] == slewStatus

        if sync:
            assert "syncBegin" in FiredEvents
            assert "syncComplete" in FiredEvents
            assert FiredEvents["syncComplete"][0] > FiredEvents["syncBegin"][0]

    def setupEvents(self):

        def slewBeginClbk(position):
            FiredEvents["slewBegin"] = (time.time(), position)

        def slewCompleteClbk(position, status):
            FiredEvents["slewComplete"] = (time.time(), position, status)

        def syncBeginClbk():
            FiredEvents["syncBegin"] = (time.time(),)

        def syncCompleteClbk():
            FiredEvents["syncComplete"] = (time.time(),)

        dome = self.manager.getProxy(self.DOME)
        dome.slewBegin += slewBeginClbk
        dome.slewComplete += slewCompleteClbk
        dome.syncBegin += syncBeginClbk
        dome.syncComplete += syncCompleteClbk

    def test_stress_dome_track(self):

        dome = self.manager.getProxy(self.DOME)
        tel = self.manager.getProxy(self.TELESCOPE)

        dome.track()

        for i in range(10):

            self.setupEvents()

            ra = f"{random.randint(7, 15)} {random.randint(0, 59)} 00"
            dec = f"{random.randint(-90, 0)} {random.randint(0, 59)} 00"
            tel.slewToRaDec(Position.fromRaDec(ra, dec))

            dome.syncWithTel()
            assertDomeAz(dome.getAz(), tel.getAz(), dome["az_resolution"])
            self.assertEvents(sync=True)

            time.sleep(random.randint(0, 10))

    pytest.mark.skip(reason="just for visual testing")

    def test_stress_dome_slew(self):
        dome = self.manager.getProxy(self.DOME)

        quit = threading.Event()

        def get_az_stress():
            while not quit.is_set():
                dome.getAz()
                time.sleep(0.5)

        az_thread = threading.Thread(target=get_az_stress)
        az_thread.start()

        for i in range(10):
            az = random.randint(0, 359)
            dome.slewToAz(Coord.fromD(az))
            time.sleep(5)

        quit.set()
        az_thread.join()

    def test_get_az(self):
        dome = self.manager.getProxy(self.DOME)
        assert dome.getAz() >= 0

    def test_slew_to_az(self):

        dome = self.manager.getProxy(self.DOME)

        start = dome.getAz()
        delta = 20

        dome.slewToAz(start + delta)

        assertDomeAz(dome.getAz(), (start + delta), dome["az_resolution"])

        with pytest.raises(InvalidDomePositionException):
            dome.slewToAz(9999)

        # event check
        self.assertEvents(DomeStatus.OK)

    def test_slit(self):

        dome = self.manager.getProxy(self.DOME)

        dome.openSlit()
        assert dome.isSlitOpen() is True

        dome.closeSlit()
        assert dome.isSlitOpen() is False


#
# setup real and fake tests
#
class TestFakeDome(FakeHardwareTest, DomeTest):

    def setup(self):

        self.manager = Manager()

        self.manager.addClass(
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

        self.manager.addClass(FakeTelescope, "fake")
        self.manager.addClass(
            FakeDome, "dome", {"telescope": "/FakeTelescope/0", "mode": "Track"}
        )
        self.TELESCOPE = "/FakeTelescope/0"
        self.DOME = "/FakeDome/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()


class TestRealDome(RealHardwareTest, DomeTest):

    def setup(self):

        self.manager = Manager()

        self.manager.addClass(
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

        self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        self.manager.addClass(
            DomeLNA40cm,
            "lna40",
            {"device": "/dev/ttyS9", "telescope": "/Meade/0", "mode": "Stand"},
        )

        self.TELESCOPE = "/Meade/meade"
        self.DOME = "/DomeLNA40cm/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()
