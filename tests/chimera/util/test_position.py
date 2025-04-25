from chimera.util.position import Position, Epoch
from chimera.util.coord import Coord
import ephem
from datetime import datetime as dt
from dateutil import tz
import pytest


def equal(a, b, e=0.0001):
    return abs(a - b) <= e


class TestPosition(object):

    def test_ra_dec(self):

        p = Position.from_ra_dec("10:00:00", "20 00 00")
        assert p.dd() == (150, 20)

        with pytest.raises(ValueError) as _:
            Position.from_ra_dec, "xyz", "abc"

    def test_alt_az(self):

        p = Position.from_alt_az("60", "200")
        assert p.dd() == (60, 200)

        with pytest.raises(ValueError) as _:
            Position.from_alt_az, "xyz", "abc"

    def test_long_lat(self):

        p = Position.from_long_lat("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_long_lat, "xyz", "abc"

    def test_galactic(self):

        p = Position.from_galactic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_galactic, "xyz", "abc"

    def test_ecliptic(self):

        p = Position.from_ecliptic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.from_ecliptic, "xyz", "abc"

    def test_alt_az_ra_dec(self):

        alt_az = Position.from_alt_az("20:30:40", "222:11:00")
        lat = Coord.from_d(0)
        o = ephem.Observer()
        o.lat = "0:0:0"
        o.long = "0:0:0"
        o.date = dt.now(tz.tzutc())
        lst = float(o.sidereal_time())
        ra_dec = Position.alt_az_to_ra_dec(alt_az, lat, lst)

        alt_az2 = Position.ra_dec_to_alt_az(ra_dec, lat, lst)
        assert equal(alt_az.alt.to_r(), alt_az2.alt.to_r()) & equal(
            alt_az.az.to_r(), alt_az2.az.to_r()
        )

    def test_distances(self):

        p1 = Position.from_ra_dec("10:00:00", "0:0:0")
        p2 = Position.from_ra_dec("12:00:00", "0:0:0")

        p1.ang_sep(p2)
        assert p1.within(p2, Coord.from_d(29.99)) is False
        assert p1.within(p2, Coord.from_d(30.01)) is True

    def test_change_epoch(self):

        sirius_j2000 = Position.from_ra_dec("06 45 08.9173", "-16 42 58.017")
        sirius_now = sirius_j2000.to_epoch(epoch=Epoch.NOW)

        print()
        print(sirius_j2000)
        print(sirius_now)
