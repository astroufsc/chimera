from datetime import datetime as dt

import ephem
import pytest
from dateutil import tz

from chimera.util.coord import Coord
from chimera.util.position import Epoch, Position, airmass


def equal(a, b, e=0.0001):
    return abs(a - b) <= e


class TestAirmass:
    def test_zenith_clamped_to_one(self):
        assert airmass(90.0) == 1.0

    def test_mid_altitudes_match_sec_z(self):
        # cross-checked against astropy AltAz.secz on real frames
        assert equal(airmass(44.07), 1.4360, 1e-3)
        assert equal(airmass(30.0), 1.9940, 1e-3)
        assert equal(airmass(10.0), 5.5860, 1e-3)

    def test_horizon_and_below_are_finite(self):
        horizon = airmass(0.0)
        assert equal(horizon, 37.920, 1e-2)
        assert airmass(-10.0) == horizon

    def test_accepts_coord(self):
        assert airmass(Coord.from_d(90.0)) == 1.0


class TestPosition:
    def test_ra_dec(self):
        p = Position.from_ra_dec("10:00:00", "20 00 00")
        assert p.dd() == (150, 20)

        with pytest.raises(ValueError) as _:
            Position.from_ra_dec("xyz", "abc")

    def test_alt_az(self):
        p = Position.from_alt_az("60", "200")
        assert p.dd() == (60, 200)

        with pytest.raises(ValueError) as _:
            Position.from_alt_az("xyz", "abc")

    def test_long_lat(self):
        p = Position.from_long_lat("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_long_lat("xyz", "abc")

    def test_galactic(self):
        p = Position.from_galactic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_galactic("xyz", "abc")

    def test_ecliptic(self):
        p = Position.from_ecliptic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_ecliptic("xyz", "abc")

    def test_alt_az_ra_dec(self):
        alt_az = Position.from_alt_az("20:30:40", "222:11:00")
        lat = 0.0
        o = ephem.Observer()
        o.lat = "0:0:0"
        o.long = "0:0:0"
        o.date = dt.now(tz.tzutc())
        lst = float(o.sidereal_time())
        ra, dec = Position.alt_az_to_ra_dec(alt_az.alt, alt_az.az, lat, lst)

        alt, az = Position.ra_dec_to_alt_az(ra, dec, lat, lst)
        assert equal(alt_az.alt, alt) & equal(alt_az.az, az)

    @pytest.mark.parametrize(
        ("lat", "dec", "alt", "az"),
        [
            # The latitude that found this: M117, -27*39:39.4. The acos
            # argument evaluates to -1.0000000000000002 here and to something
            # inside the domain at -27.6 and at -22.5, so the crash rides on
            # the site and nothing but the right site reveals it.
            (-27.660833, -90.0, 27.660833, 180.0),
            (-27.6, -90.0, 27.6, 180.0),
            (-22.5, -90.0, 22.5, 180.0),
            # The other pole, and the northern hemisphere, for symmetry.
            (45.0, 90.0, 45.0, 0.0),
            (-27.660833, 90.0, -27.660833, 0.0),
        ],
    )
    def test_a_pole_does_not_raise_a_math_domain_error(self, lat, dec, alt, az):
        """The visible pole sits at an altitude of the latitude, due south of a
        southern observer and due north of a northern one.

        `coord_rotate` reaches `asin` and `acos` arguments that are exactly +-1
        there, and floating point puts them just outside, which raised
        `ValueError: math domain error` for any RA. A mount parked at the pole
        asks for this on every poll.
        """
        got_alt, got_az = Position.ra_dec_to_alt_az(6.0, dec, lat, 0.0)
        assert equal(got_alt, alt, 1e-6)
        assert equal(got_az, az, 1e-6)

    def test_distances(self):
        p1 = Position.from_ra_dec("10:00:00", "0:0:0")
        p2 = Position.from_ra_dec("12:00:00", "0:0:0")

        p1.angsep(p2)
        assert p1.within(p2, Coord.from_d(29.99)) is False
        assert p1.within(p2, Coord.from_d(30.01)) is True

    def test_distances_in_alt_az(self):
        """from_alt_az stores (alt, az) - latitude first - while gcdist
        reads its pair as (longitude, latitude). Passing the stored order
        straight through called two points 2 degrees apart at the zenith
        180 degrees apart."""
        zenith_north = Position.from_alt_az(89, 0)
        zenith_south = Position.from_alt_az(89, 180)
        assert equal(float(zenith_north.angsep(zenith_south)), 2.0, 1e-6)

        # a degree of altitude is a degree of separation, anywhere
        assert equal(
            float(Position.from_alt_az(80, 78).angsep(Position.from_alt_az(81, 78))),
            1.0,
            1e-6,
        )

        # a degree of azimuth is less than a degree of separation, by
        # roughly cos(alt): 1.04143 deg from the spherical law of cosines
        assert equal(
            float(Position.from_alt_az(80, 78).angsep(Position.from_alt_az(80, 84))),
            1.04143,
            1e-5,
        )

        near_zenith = Position.from_alt_az(89, 0)
        assert near_zenith.within(zenith_south, Coord.from_d(2.01)) is True
        assert near_zenith.within(zenith_south, Coord.from_d(1.99)) is False

    def test_distance_between_different_systems_is_refused(self):
        with pytest.raises(ValueError):
            Position.from_alt_az(45, 90).angsep(
                Position.from_ra_dec("10:00:00", "0:0:0")
            )

    def test_change_epoch(self):
        sirius_j2000 = Position.from_ra_dec("06 45 08.9173", "-16 42 58.017")
        sirius_now = sirius_j2000.to_epoch(epoch=Epoch.NOW)

        print()
        print(sirius_j2000)
        print(sirius_now)
