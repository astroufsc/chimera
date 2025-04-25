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


def assert_eps_equal(a, b, e=60):
    """Assert wether a equals b withing eps precision, in
    arcseconds. Both a and b must be Coords.
    """
    assert abs(a.AS - b.AS) <= e


chimera.core.log.set_console_level(int(1e10))
log = logging.getLogger("chimera.tests")

# hack for event triggering asserts
fired_events = {}


class TelescopeTest(object):

    telescope = ""

    def assert_events(self, slew_status):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        assert "slew_begin" in fired_events
        assert isinstance(fired_events["slew_begin"][1], Position)

        assert "slew_complete" in fired_events
        assert fired_events["slew_complete"][0] > fired_events["slew_begin"][0]
        assert isinstance(fired_events["slew_complete"][1], Position)
        assert fired_events["slew_complete"][2] in TelescopeStatus
        assert fired_events["slew_complete"][2] == slew_status

    def setup_events(self):

        def slew_begin_callback(position):
            fired_events["slew_begin"] = (time.time(), position)

        def slew_complete_callback(position, status):
            fired_events["slew_complete"] = (time.time(), position, status)

        tel = self.manager.get_proxy(self.telescope)
        tel.slew_begin += slew_begin_callback
        tel.slew_complete += slew_complete_callback

    def test_slew(self):

        site = self.manager.get_proxy("/Site/0")

        dest = Position.from_ra_dec(site.LST(), site["latitude"])
        real_dest = None

        def slew_begin_callback(target):
            global real_dest
            real_dest = target

        def slew_complete_callback(position, status):
            assert_eps_equal(position.ra, real_dest.ra, 60)
            assert_eps_equal(position.dec, real_dest.dec, 60)

        self.tel.slew_begin += slew_begin_callback
        self.tel.slew_complete += slew_complete_callback

        self.tel.slew_to_ra_dec(dest)

        # event checkings
        self.assert_events(TelescopeStatus.OK)

    def test_slew_abort(self):

        site = self.manager.get_proxy("/Site/0")

        # go to know position
        self.tel.slew_to_ra_dec(Position.from_ra_dec(site.LST(), site["latitude"]))
        last = self.tel.get_position_ra_dec()

        # clear event checkings

        # drift it
        dest = Position.from_ra_dec(
            last.ra + Coord.from_h(1), last.dec + Coord.from_d(10)
        )
        real_dest = None

        def slew_begin_callback(target):
            global real_dest
            real_dest = target

        def slew_complete_callback(position, status):
            assert last.ra < position.ra < real_dest.ra
            assert last.dec < position.dec < real_dest.dec

        self.tel.slew_begin += slew_begin_callback
        self.tel.slew_complete += slew_complete_callback

        # async slew
        def slew():
            tel = self.manager.get_proxy(self.telescope)
            tel.slew_to_ra_dec(dest)

        pool = ThreadPoolExecutor()
        slew_future = pool.submit(slew)

        # wait thread to be scheduled
        time.sleep(2)

        # abort and test
        self.tel.abort_slew()

        wait([slew_future])

        # event checkings
        self.assert_events(TelescopeStatus.ABORTED)

    def test_sync(self):

        # get current position, drift the scope, and sync on the first
        # position (like done when aligning the telescope).

        real = self.tel.get_position_ra_dec()

        def sync_complete_callback(position):
            assert position.ra == real.ra
            assert position.dec == real.dec

        self.tel.sync_complete += sync_complete_callback

        # drift to "real" object coordinate
        drift = Position.from_ra_dec(
            real.ra + Coord.from_h(1), real.dec + Coord.from_d(1)
        )
        self.tel.slew_to_ra_dec(drift)

        self.tel.sync_ra_dec(real)

        time.sleep(2)

    @pytest.mark.skip
    def test_park(self):

        def print_position():
            print(self.tel.get_position_ra_dec(), self.tel.get_position_alt_az())
            sys.stdout.flush()

        print()

        ra = self.tel.get_ra()
        dec = self.tel.get_dec()

        print("current position:", self.tel.get_position_ra_dec())
        print("moving to:", (ra - "01 00 00"), (dec - "01 00 00"))

        self.tel.slew_to_ra_dec(
            Position.from_ra_dec(ra - Coord.from_h(1), dec - Coord.from_d(1))
        )

        for i in range(10):
            print_position()
            time.sleep(0.5)

        print("parking...")
        sys.stdout.flush()
        self.tel.park()

        t0 = time.time()
        wait = 30

        for i in range(10):
            print_position()
            time.sleep(0.5)

        while time.time() < t0 + wait:
            print("\rwaiting ... ", end=" ")
            sys.stdout.flush()
            time.sleep(1)

        print("unparking...")
        sys.stdout.flush()

        self.tel.unpark()

        for i in range(10):
            print_position()
            time.sleep(0.5)

    pytest.mark.skip("FIXME: make a real test.")

    def test_jog(self):

        print()

        dt = Coord.from_dms("00:20:00")

        start = self.tel.get_position_ra_dec()
        self.tel.move_north(dt, SlewRate.FIND)
        print(
            "North:",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_south(dt, SlewRate.FIND)
        print(
            "South:",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_west(dt, SlewRate.FIND)
        print(
            "West :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_east(dt, SlewRate.FIND)
        print(
            "East :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_north(dt, SlewRate.FIND)
        self.tel.move_east(dt, SlewRate.FIND)
        print(
            "NE   :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_south(dt, SlewRate.FIND)
        self.tel.move_east(dt, SlewRate.FIND)
        print(
            "SE   :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_north(dt, SlewRate.FIND)
        self.tel.move_west(dt, SlewRate.FIND)
        print(
            "NW   :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )

        start = self.tel.get_position_ra_dec()
        self.tel.move_south(dt, SlewRate.FIND)
        self.tel.move_west(dt, SlewRate.FIND)
        print(
            "SW   :",
            (start.ra - self.tel.get_position_ra_dec().ra).AS,
            (start.dec - self.tel.get_position_ra_dec().dec).AS,
        )


#
# setup real and fake tests
#
class TestFakeTelescope(FakeHardwareTest, TelescopeTest):

    def setup(self):

        self.manager = Manager(port=8000)

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

        self.manager.add_class(FakeTelescope, "fake")
        self.telescope = "/FakeTelescope/0"

        self.tel = self.manager.get_proxy(self.telescope)

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()


class TestRealTelescope(RealHardwareTest, TelescopeTest):

    def setup(self):

        self.manager = Manager(port=8000)

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

        from chimera.instruments.meade import Meade

        self.manager.add_class(Meade, "meade", {"device": "/dev/ttyS6"})
        self.telescope = "/Meade/0"
        # self.telescope = "150.162.110.3:7666/TheSkyTelescope/0"
        self.tel = self.manager.get_proxy(self.telescope)

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()
