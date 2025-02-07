# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from concurrent.futures import ThreadPoolExecutor, wait
import time
import sys
import logging

import pytest

from chimera.core.manager import Manager
from chimera.core.site import Site

from chimera.util.coord import Coord
from chimera.util.position import Position

from chimera.interfaces.telescope import SlewRate, TelescopeStatus

from .base import FakeHardwareTest, RealHardwareTest

import chimera.core.log


def assertEpsEqual(a, b, e=60):
    """Assert wether a equals b withing eps precision, in
    arcseconds. Both a and b must be Coords.
    """
    assert abs(a.AS - b.AS) <= e


chimera.core.log.setConsoleLevel(int(1e10))
log = logging.getLogger("chimera.tests")

# hack for event  triggering asserts
FiredEvents = {}


class TelescopeTest(object):

    TELESCOPE = ""

    def assertEvents(self, slewStatus):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        assert "slewBegin" in FiredEvents
        assert isinstance(FiredEvents["slewBegin"][1], Position)

        assert "slewComplete" in FiredEvents
        assert FiredEvents["slewComplete"][0] > FiredEvents["slewBegin"][0]
        assert isinstance(FiredEvents["slewComplete"][1], Position)
        assert FiredEvents["slewComplete"][2] in TelescopeStatus
        assert FiredEvents["slewComplete"][2] == slewStatus

    def setupEvents(self):

        def slewBeginClbk(position):
            FiredEvents["slewBegin"] = (time.time(), position)

        def slewCompleteClbk(position, status):
            FiredEvents["slewComplete"] = (time.time(), position, status)

        tel = self.manager.getProxy(self.TELESCOPE)
        tel.slewBegin += slewBeginClbk
        tel.slewComplete += slewCompleteClbk

    def test_slew(self):

        site = self.manager.getProxy("/Site/0")

        dest = Position.fromRaDec(site.LST(), site["latitude"])
        real_dest = None

        def slewBeginClbk(target):
            global real_dest
            real_dest = target

        def slewCompleteClbk(position, status):
            assertEpsEqual(position.ra, real_dest.ra, 60)
            assertEpsEqual(position.dec, real_dest.dec, 60)

        self.tel.slewBegin += slewBeginClbk
        self.tel.slewComplete += slewCompleteClbk

        self.tel.slewToRaDec(dest)

        # event checkings
        self.assertEvents(TelescopeStatus.OK)

    def test_slew_abort(self):

        site = self.manager.getProxy("/Site/0")

        # go to know position
        self.tel.slewToRaDec(Position.fromRaDec(site.LST(), site["latitude"]))
        last = self.tel.getPositionRaDec()

        # clear event checkings

        # drift it
        dest = Position.fromRaDec(last.ra + Coord.fromH(1), last.dec + Coord.fromD(10))
        real_dest = None

        def slewBeginClbk(target):
            global real_dest
            real_dest = target

        def slewCompleteClbk(position, status):
            assert last.ra < position.ra < real_dest.ra
            assert last.dec < position.dec < real_dest.dec

        self.tel.slewBegin += slewBeginClbk
        self.tel.slewComplete += slewCompleteClbk

        # async slew
        def slew():
            tel = self.manager.getProxy(self.TELESCOPE)
            tel.slewToRaDec(dest)

        pool = ThreadPoolExecutor()
        slew_future = pool.submit(slew)

        # wait thread to be scheduled
        time.sleep(2)

        # abort and test
        self.tel.abortSlew()

        wait([slew_future])

        # event checkings
        self.assertEvents(TelescopeStatus.ABORTED)

    def test_sync(self):

        # get current position, drift the scope, and sync on the first
        # position (like done when aligning the telescope).

        real = self.tel.getPositionRaDec()

        def syncCompleteClbk(position):
            assert position.ra == real.ra
            assert position.dec == real.dec

        self.tel.syncComplete += syncCompleteClbk

        # drift to "real" object coordinate
        drift = Position.fromRaDec(real.ra + Coord.fromH(1), real.dec + Coord.fromD(1))
        self.tel.slewToRaDec(drift)

        self.tel.syncRaDec(real)

        time.sleep(2)

    @pytest.mark.skip
    def test_park(self):

        def printPosition():
            print(self.tel.getPositionRaDec(), self.tel.getPositionAltAz())
            sys.stdout.flush()

        print()

        ra = self.tel.getRa()
        dec = self.tel.getDec()

        print("current position:", self.tel.getPositionRaDec())
        print("moving to:", (ra - "01 00 00"), (dec - "01 00 00"))

        self.tel.slewToRaDec(
            Position.fromRaDec(ra - Coord.fromH(1), dec - Coord.fromD(1))
        )

        for i in range(10):
            printPosition()
            time.sleep(0.5)

        print("parking...")
        sys.stdout.flush()
        self.tel.park()

        t0 = time.time()
        wait = 30

        for i in range(10):
            printPosition()
            time.sleep(0.5)

        while time.time() < t0 + wait:
            print("\rwaiting ... ", end=" ")
            sys.stdout.flush()
            time.sleep(1)

        print("unparking...")
        sys.stdout.flush()

        self.tel.unpark()

        for i in range(10):
            printPosition()
            time.sleep(0.5)

    pytest.mark.skip("FIXME: make a real test.")

    def test_jog(self):

        print()

        dt = Coord.fromDMS("00:20:00")

        start = self.tel.getPositionRaDec()
        self.tel.moveNorth(dt, SlewRate.FIND)
        print(
            "North:",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveSouth(dt, SlewRate.FIND)
        print(
            "South:",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveWest(dt, SlewRate.FIND)
        print(
            "West :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveEast(dt, SlewRate.FIND)
        print(
            "East :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveNorth(dt, SlewRate.FIND)
        self.tel.moveEast(dt, SlewRate.FIND)
        print(
            "NE   :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveSouth(dt, SlewRate.FIND)
        self.tel.moveEast(dt, SlewRate.FIND)
        print(
            "SE   :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveNorth(dt, SlewRate.FIND)
        self.tel.moveWest(dt, SlewRate.FIND)
        print(
            "NW   :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )

        start = self.tel.getPositionRaDec()
        self.tel.moveSouth(dt, SlewRate.FIND)
        self.tel.moveWest(dt, SlewRate.FIND)
        print(
            "SW   :",
            (start.ra - self.tel.getPositionRaDec().ra).AS,
            (start.dec - self.tel.getPositionRaDec().dec).AS,
        )


#
# setup real and fake tests
#
class TestFakeTelescope(FakeHardwareTest, TelescopeTest):

    def setup(self):

        self.manager = Manager(port=8000)

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

        self.manager.addClass(FakeTelescope, "fake")
        self.TELESCOPE = "/FakeTelescope/0"

        self.tel = self.manager.getProxy(self.TELESCOPE)

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()


class TestRealTelescope(RealHardwareTest, TelescopeTest):

    def setup(self):

        self.manager = Manager(port=8000)

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

        from chimera.instruments.meade import Meade

        self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        self.TELESCOPE = "/Meade/0"
        # self.TELESCOPE = "150.162.110.3:7666/TheSkyTelescope/0"
        self.tel = self.manager.getProxy(self.TELESCOPE)

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()
