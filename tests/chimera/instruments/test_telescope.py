# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import logging
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from types import SimpleNamespace

import pytest

import chimera.core.log
from chimera.core.exceptions import ChimeraException
from chimera.instruments.faketelescope import FakeTelescope
from chimera.instruments.telescope import TelescopeBase, axes
from chimera.interfaces.telescope import TelescopePierSide, TelescopeStatus
from chimera.util.coord import Coord
from chimera.util.position import Epoch, Position

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


def slew_begin_callback(ra, dec, epoch=None):
    # epoch defaults to None: slew_to_ra_dec publishes (ra, dec, epoch) but
    # the alt/az and move_* slews still publish only (ra, dec)
    fired_events["slew_begin"] = (time.time(), ra, dec, epoch)


def slew_complete_callback(ra, dec, status):
    fired_events["slew_complete"] = (time.time(), ra, dec, status)


@pytest.fixture
def telescope(manager):
    # the manager fixture provides the injected site (latitude matches
    # SITE_LATITUDE above)
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


def test_jog_wraps_ra_at_the_clock(monkeypatch):
    """A jog either side of 0 h stays on the clock: RA 0.05 h jogged 6 minutes
    west is 23.95 h, not the negative RA Position refuses to be built from."""
    telescope = FakeTelescope()
    monkeypatch.setattr(
        telescope,
        "get_site",
        lambda: SimpleNamespace(ra_dec_to_alt_az=lambda ra, dec: (60.0, 30.0)),
    )
    for event in ("slew_begin", "slew_complete"):
        monkeypatch.setattr(FakeTelescope, event, lambda *args: None, raising=False)

    telescope._ra, telescope._dec = 0.05, -30.0
    six_minutes = float(Coord.from_h(0.1).to_as())

    telescope.move_west(six_minutes)
    assert telescope.get_ra() == pytest.approx(23.95)

    telescope.move_east(six_minutes)
    assert telescope.get_ra() == pytest.approx(0.05)


class TestFakeTelescopePierSide:
    """FakeTelescope derives both sides from the hour angle instead of
    reporting UNKNOWN forever: `h < 0` is WEST (the AM5 simulator's rule),
    WEST is declared NORMAL, and a pin from set_pier_side lasts until the
    next slew."""

    LST_H = 6.0

    @pytest.fixture
    def telescope(self, monkeypatch):
        telescope = FakeTelescope()
        site = SimpleNamespace(
            lst_in_rads=lambda: self.LST_H * math.pi / 12.0,
            ra_dec_to_alt_az=lambda ra, dec: (60.0, 30.0),
        )
        monkeypatch.setattr(telescope, "get_site", lambda: site)
        for event in ("slew_begin", "slew_complete"):
            monkeypatch.setattr(FakeTelescope, event, lambda *args: None, raising=False)
        telescope._dec = -30.0
        return telescope

    def test_west_of_the_meridian_is_west_and_normal(self, telescope):
        telescope._ra = self.LST_H - 3.0  # h = +3 h: already past the meridian
        assert telescope.get_pier_side() == TelescopePierSide.EAST
        assert telescope.get_mount_side() == TelescopePierSide.BEYOND

        telescope._ra = self.LST_H + 3.0  # h = -3 h: still rising
        assert telescope.get_pier_side() == TelescopePierSide.WEST
        assert telescope.get_mount_side() == TelescopePierSide.NORMAL

    def test_the_hour_angle_wraps_like_a_clock(self, telescope):
        telescope._ra = (self.LST_H + 14.0) % 24.0  # h = -14 h, which is +10 h
        assert telescope.get_pier_side() == TelescopePierSide.EAST

    def test_a_pinned_side_lasts_until_the_next_slew(self, telescope):
        telescope._ra = self.LST_H + 3.0
        assert telescope.get_pier_side() == TelescopePierSide.WEST

        telescope.set_pier_side(TelescopePierSide.EAST)
        assert telescope.get_pier_side() == TelescopePierSide.EAST
        assert telescope.get_mount_side() == TelescopePierSide.BEYOND

        telescope.move_east(float(Coord.from_h(0.1).to_as()))
        assert telescope.get_pier_side() == TelescopePierSide.WEST

    def test_without_a_site_the_side_is_unknown(self, telescope, monkeypatch):
        def no_site():
            raise RuntimeError("no bus")

        monkeypatch.setattr(telescope, "get_site", no_site)
        assert telescope.get_pier_side() == TelescopePierSide.UNKNOWN
        assert telescope.get_mount_side() == TelescopePierSide.UNKNOWN


# ---------------------------------------------------------------------------
# Automatic pier flip (unit level, no bus): TelescopeBase.control() re-slews a
# mount that tracked past pier_flip_ha.
# ---------------------------------------------------------------------------


class PierTelescope(TelescopeBase):
    """Just enough telescope to drive the pier flip check by hand."""

    def __init__(self):
        TelescopeBase.__init__(self)

        self.ha = -1.0  # hour angle the site will report, in hours
        self.tracking = True
        self.slewing = False
        self.slews = []
        self.controls = 0
        self.slew_error = None
        self.hour_angle_args = []

    def _control(self):
        self.controls += 1
        return True

    def is_slewing(self):
        return self.slewing

    def is_tracking(self):
        return self.tracking

    def get_ra(self):
        return 12.0

    def get_dec(self):
        return -30.0

    def get_position_ra_dec(self):
        return self.get_ra(), self.get_dec()

    def slew_to_ra_dec(self, ra, dec, epoch=2000):
        if self.slew_error is not None:
            raise self.slew_error
        self.slews.append((ra, dec, epoch))


@pytest.fixture
def pier_telescope(monkeypatch):
    def factory(**config):
        telescope = PierTelescope()
        for key, value in config.items():
            telescope[key] = value

        def ra_to_ha(ra):
            telescope.hour_angle_args.append(ra)
            return telescope.ha

        monkeypatch.setattr(
            telescope, "get_site", lambda: SimpleNamespace(ra_to_ha=ra_to_ha)
        )
        return telescope

    return factory


class TestPierFlip:
    def test_disabled_by_default(self, pier_telescope):
        telescope = pier_telescope()

        telescope.ha = -0.1
        telescope.control()
        telescope.ha = +0.1
        telescope.control()

        assert telescope.slews == []
        # the driver's own periodic work still runs on every cycle
        assert telescope.controls == 2

    def test_tracking_past_the_limit_flips(self, pier_telescope):
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = -0.1
        telescope.control()
        assert telescope.slews == []

        telescope.ha = +0.1
        telescope.control()
        # same position, same epoch the position accessors answer in: the
        # mount changes side of pier, not target
        assert telescope.slews == [(12.0, -30.0, 2000)]

    def test_the_hour_angle_is_measured_in_the_epoch_of_date(self, pier_telescope):
        """The position accessors answer in J2000; the local sidereal time an
        hour angle is measured against is epoch of date. Subtracting one from
        the other is 26 years of precession out -- ~2 minutes of time in 2026,
        and more every year -- so the flip fires early."""
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.control()

        (ra,) = telescope.hour_angle_args
        of_date = Position.from_ra_dec(12.0, -30.0, epoch=Epoch.J2000).to_epoch(
            Epoch.NOW
        )
        assert ra == pytest.approx(float(of_date.ra.to_h()))
        # a quarter century of precession, not the J2000 number it started from
        assert 0.01 < ra - 12.0 < 0.05

    def test_flips_only_once(self, pier_telescope):
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = -0.1
        telescope.control()

        for telescope.ha in (0.1, 0.2, 0.3):
            telescope.control()

        assert telescope.slews == [(12.0, -30.0, 2000)]

    def test_a_slew_past_the_limit_does_not_flip(self, pier_telescope):
        """The mount never tracked into the limit: the driver put it on
        whichever side it wanted when it slewed there."""
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = +1.0
        telescope.control()
        telescope.ha = +1.5
        telescope.control()

        assert telescope.slews == []

    def test_slewing_disarms_the_flip(self, pier_telescope):
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = -0.1
        telescope.control()

        telescope.slewing = True
        telescope.ha = +0.1
        telescope.control()

        telescope.slewing = False
        telescope.control()

        assert telescope.slews == []

    def test_a_parked_mount_is_not_flipped(self, pier_telescope):
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = -0.1
        telescope.control()

        telescope.tracking = False
        telescope.ha = +0.1
        telescope.control()

        assert telescope.slews == []

    def test_the_limit_is_configurable(self, pier_telescope):
        telescope = pier_telescope(pier_flip_ha=0.5)

        for telescope.ha in (-0.1, 0.1, 0.4):
            telescope.control()
        assert telescope.slews == []

        telescope.ha = 0.6
        telescope.control()
        assert telescope.slews == [(12.0, -30.0, 2000)]

    def test_a_failed_flip_is_retried(self, pier_telescope):
        """The mount is tracking into the pier: giving up quietly is the one
        thing the check must not do."""
        telescope = pier_telescope(pier_flip_ha=0)

        telescope.ha = -0.1
        telescope.control()

        telescope.slew_error = ChimeraException("mount is not answering")
        telescope.ha = +0.1
        with pytest.raises(ChimeraException):
            telescope.control()
        assert telescope.slews == []

        telescope.slew_error = None
        telescope.control()
        assert telescope.slews == [(12.0, -30.0, 2000)]


class TestAxesHelper:
    """The axis-vocabulary helper in chimera.instruments.telescope.

    The axis interfaces take one canonical (roll, pitch) pair so the WS
    schema stays typed; `axes` is what lets a call site read in whichever
    vocabulary its author thinks in.
    """

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"roll": 1.5, "pitch": -2.5},
            {"ha": 1.5, "dec": -2.5},
            {"az": 1.5, "alt": -2.5},
            {"axis1": 1.5, "axis2": -2.5},
            {"primary": 1.5, "secondary": -2.5},
        ],
        ids=["roll_pitch", "ha_dec", "az_alt", "axis1_axis2", "primary_secondary"],
    )
    def test_every_vocabulary_normalises_to_roll_pitch(self, kwargs):
        assert axes(**kwargs) == (1.5, -2.5)

    def test_zero_is_a_value_not_an_absence(self):
        # The whole point of set_axis_rate(0, 0) is "stop offsetting", so a
        # falsy-but-present rate must survive.
        assert axes(roll=0.0, pitch=0.0) == (0.0, 0.0)
        assert axes(ha=0.0, dec=-1.0) == (0.0, -1.0)

    def test_no_arguments_is_an_error(self):
        with pytest.raises(ValueError, match="needs one pair"):
            axes()

    @pytest.mark.parametrize(
        "kwargs", [{"ha": 1.0}, {"dec": 1.0}, {"roll": 1.0}, {"secondary": 1.0}]
    )
    def test_half_a_pair_is_an_error(self, kwargs):
        with pytest.raises(ValueError, match="without"):
            axes(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"ha": 1.0, "alt": 2.0},
            {"roll": 1.0, "pitch": 2.0, "az": 3.0},
            {"axis1": 1.0, "secondary": 2.0},
        ],
    )
    def test_mixing_vocabularies_is_an_error(self, kwargs):
        # Deliberately not resolved by precedence: asking in two vocabularies
        # at once is a bug in the caller, and picking a winner would hide it.
        with pytest.raises(ValueError, match="mixes axis vocabularies"):
            axes(**kwargs)


class TestTelescopeBaseAxisStubs:
    """TelescopeBase gained three interfaces; a driver that does not
    implement them should fail honestly rather than silently."""

    @pytest.mark.parametrize(
        "call",
        [
            lambda t: t.get_axis_counts(),
            lambda t: t.get_axis_scale(),
            lambda t: t.set_axis_rate(0.0, 0.0),
            lambda t: t.get_axis_rate(),
            lambda t: t.clear_pointing_model(),
            lambda t: t.apply_pointing_model(0.0, 0.0),
        ],
    )
    def test_unimplemented_axis_methods_raise(self, call):
        assert issubclass(FakeTelescope, TelescopeBase)
        with pytest.raises(NotImplementedError):
            call(FakeTelescope())
