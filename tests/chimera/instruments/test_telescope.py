# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait

import pytest

import chimera.core.log
from chimera.core.site import Site
from chimera.instruments.faketelescope import FakeTelescope
from chimera.interfaces.telescope import TelescopeStatus
from chimera.util.coord import Coord

chimera.core.log.set_console_level(int(1e10))
log = logging.getLogger("chimera.tests")

SITE_LATITUDE = float(Coord.from_dms("-27 36 13").to_d())


def assert_eps_equal(a, b, e=60):
    """Assert whether a equals b within eps precision, in arcseconds.
    Both a and b are in degrees.
    """
    assert abs(a - b) * 3600 <= e


# hack for event triggering asserts
fired_events = {}


def slew_begin_callback(ra, dec):
    fired_events["slew_begin"] = (time.time(), ra, dec)


def slew_complete_callback(ra, dec, status):
    fired_events["slew_complete"] = (time.time(), ra, dec, status)


@pytest.fixture
def telescope(manager):
    manager.add_class(
        Site,
        "lna",
        {
            "name": "UFSC",
            "latitude": "-27 36 13",
            "longitude": "-48 31 20",
            "altitude": "20",
        },
    )

    manager.add_class(FakeTelescope, "fake")

    fired_events.clear()

    tel = manager.get_proxy("/FakeTelescope/0")
    tel.slew_begin += slew_begin_callback
    tel.slew_complete += slew_complete_callback

    return tel


class TestFakeTelescope:
    def assert_events(self, slew_status):
        # for every slew, we need to check if all events were fired with the
        # right parameters.
        # NOTE: no delivery-time ordering asserts: events are delivered
        # asynchronously and the bus does not guarantee cross-event callback
        # ordering

        assert "slew_begin" in fired_events
        assert isinstance(fired_events["slew_begin"][1], (int, float))
        assert isinstance(fired_events["slew_begin"][2], (int, float))

        assert "slew_complete" in fired_events
        assert isinstance(fired_events["slew_complete"][1], (int, float))
        assert isinstance(fired_events["slew_complete"][2], (int, float))
        assert fired_events["slew_complete"][3] in TelescopeStatus
        assert fired_events["slew_complete"][3] == slew_status

    def goto_safe_position(self, telescope):
        # slew to a high altitude position, so relative slews keep the
        # telescope above the minimum altitude limit
        telescope.slew_to_alt_az(60.0, 30.0)

    def test_slew(self, telescope, wait_for):
        self.goto_safe_position(telescope)
        ra, dec = telescope.get_position_ra_dec()

        fired_events.clear()

        dest_ra = ra + 0.5  # hours
        dest_dec = dec + 2  # degrees

        telescope.slew_to_ra_dec(dest_ra, dest_dec)

        ra, dec = telescope.get_position_ra_dec()
        assert_eps_equal(ra * 15, dest_ra * 15, 60)
        assert_eps_equal(dec, dest_dec, 60)

        # event checkings
        assert wait_for(lambda: "slew_complete" in fired_events)
        self.assert_events(TelescopeStatus.OK)

    def test_slew_abort(self, telescope, manager, wait_for):
        # go to known position
        self.goto_safe_position(telescope)
        last_ra, last_dec = telescope.get_position_ra_dec()

        fired_events.clear()

        # drift it
        dest_ra = last_ra + 1  # hours
        dest_dec = last_dec + 10  # degrees

        # async slew
        def slew():
            tel = manager.get_proxy("/FakeTelescope/0")
            tel.slew_to_ra_dec(dest_ra, dest_dec)

        pool = ThreadPoolExecutor()
        slew_future = pool.submit(slew)

        # wait thread to be scheduled
        time.sleep(2)

        # abort and test
        telescope.abort_slew()

        wait([slew_future])

        # aborted mid-way: position must be between start and destination
        ra, dec = telescope.get_position_ra_dec()
        assert last_ra < ra < dest_ra
        assert last_dec < dec < dest_dec

        # event checkings
        assert wait_for(lambda: "slew_complete" in fired_events)
        self.assert_events(TelescopeStatus.ABORTED)

    def test_sync(self, telescope):
        # get current position, drift the scope, and sync on the first
        # position (like done when aligning the telescope).

        self.goto_safe_position(telescope)
        real_ra, real_dec = telescope.get_position_ra_dec()

        # drift to "real" object coordinate
        telescope.slew_to_ra_dec(real_ra + 0.5, real_dec + 1)

        telescope.sync_ra_dec(real_ra, real_dec)

        ra, dec = telescope.get_position_ra_dec()
        assert_eps_equal(ra * 15, real_ra * 15, 60)
        assert_eps_equal(dec, real_dec, 60)

    @pytest.mark.skip
    def test_park(self, telescope):
        def print_position():
            print(telescope.get_position_ra_dec(), telescope.get_position_alt_az())
            sys.stdout.flush()

        print()

        ra, dec = telescope.get_position_ra_dec()

        print("current position:", (ra, dec))
        print("moving to:", (ra - 1, dec - 1))

        telescope.slew_to_ra_dec(ra - 1, dec - 1)

        for i in range(10):
            print_position()
            time.sleep(0.5)

        print("parking...")
        sys.stdout.flush()
        telescope.park()

        t0 = time.time()
        timeout = 30

        for i in range(10):
            print_position()
            time.sleep(0.5)

        while time.time() < t0 + timeout:
            print("\rwaiting ... ", end=" ")
            sys.stdout.flush()
            time.sleep(1)

        print("unparking...")
        sys.stdout.flush()

        telescope.unpark()

        for i in range(10):
            print_position()
            time.sleep(0.5)

    def test_jog(self, telescope):
        print()

        self.goto_safe_position(telescope)

        dt = float(Coord.from_dms("00:20:00").to_as())  # offset in arcseconds

        for direction in ("north", "south", "east", "west"):
            start_ra, start_dec = telescope.get_position_ra_dec()
            getattr(telescope, f"move_{direction}")(dt)
            ra, dec = telescope.get_position_ra_dec()
            print(
                f"{direction}:",
                (start_ra - ra) * 15 * 3600,
                (start_dec - dec) * 3600,
            )
            assert (start_ra, start_dec) != (ra, dec)
