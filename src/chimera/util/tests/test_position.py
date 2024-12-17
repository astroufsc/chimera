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

        p = Position.fromRaDec("10:00:00", "20 00 00")
        assert p.dd() == (150, 20)

        with pytest.raises(ValueError) as _:
            Position.fromRaDec, "xyz", "abc"

    def test_alt_az(self):

        p = Position.fromAltAz("60", "200")
        assert p.dd() == (60, 200)

        with pytest.raises(ValueError) as _:
            Position.fromAltAz, "xyz", "abc"

    def test_long_lat(self):

        p = Position.fromLongLat("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.fromLongLat, "xyz", "abc"

    def test_galactic(self):

        p = Position.fromGalactic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.fromGalactic, "xyz", "abc"

    def test_ecliptic(self):

        p = Position.fromEcliptic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        with pytest.raises(ValueError) as _:
            Position.fromEcliptic, "xyz", "abc"

    def test_altAzRaDec(self):

        altAz = Position.fromAltAz("20:30:40", "222:11:00")
        lat = Coord.fromD(0)
        o = ephem.Observer()
        o.lat = "0:0:0"
        o.long = "0:0:0"
        o.date = dt.now(tz.tzutc())
        lst = float(o.sidereal_time())
        raDec = Position.altAzToRaDec(altAz, lat, lst)

        altAz2 = Position.raDecToAltAz(raDec, lat, lst)
        assert equal(altAz.alt.toR(), altAz2.alt.toR()) & equal(
            altAz.az.toR(), altAz2.az.toR()
        )

    def test_distances(self):

        p1 = Position.fromRaDec("10:00:00", "0:0:0")
        p2 = Position.fromRaDec("12:00:00", "0:0:0")

        p1.angsep(p2)
        assert p1.within(p2, Coord.fromD(29.99)) is False
        assert p1.within(p2, Coord.fromD(30.01)) is True

    def test_changeEpoch(self):

        sirius_j2000 = Position.fromRaDec("06 45 08.9173", "-16 42 58.017")
        sirius_now = sirius_j2000.toEpoch(epoch=Epoch.NOW)

        print()
        print(sirius_j2000)
        print(sirius_now)
