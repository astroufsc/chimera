

from nose.tools import assert_raises

from chimera.util.position import Position
from chimera.util.coord import Coord
import ephem
from datetime import datetime as dt
from dateutil import tz

def equal (a, b, e=0.0001):
    return ( abs(a-b) <= e)

class TestPosition (object):

    def test_ra_dec (self):

        p = Position.fromRaDec("10:00:00", "20 00 00")
        assert p.dd() == (150, 20)

        assert_raises(ValueError, Position.fromRaDec, "xyz", "abc")

    def test_alt_az (self):

        p = Position.fromAltAz("60", "200")
        assert p.dd() == (60, 200)

        assert_raises(ValueError, Position.fromAltAz, "xyz", "abc")        

    def test_long_lat (self):

        p = Position.fromLongLat("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        assert_raises(ValueError, Position.fromLongLat, "xyz", "abc")        

    def test_galactic (self):

        p = Position.fromGalactic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        assert_raises(ValueError, Position.fromGalactic, "xyz", "abc")        

    def test_ecliptic (self):

        p = Position.fromEcliptic("-27 30", "-48 00")
        assert p.dd() == (-27.5, -48.0)

        assert_raises(ValueError, Position.fromEcliptic, "xyz", "abc")        

    def test_altAzRaDec(self):
        
        altAz = Position.fromAltAz('20:30:40', '222:11:00')
        lat = Coord.fromD(0)
        o = ephem.Observer()
        o.lat = '0:0:0'
        o.long = '0:0:0'
        o.date = dt.now(tz.tzutc())
        lst = float(o.sidereal_time())
        raDec = Position.altAzToRaDec(altAz, lat, lst)
        
        altAz2 = Position.raDecToAltAz(raDec, lat, lst)
        assert equal(altAz.alt.toR(),altAz2.alt.toR()) & equal(altAz.az.toR(),altAz2.az.toR())

    def test_distances(self):

        p1 = Position.fromRaDec("10:00:00", "0:0:0")
        p2 = Position.fromRaDec("12:00:00", "0:0:0")

        d = p1.angsep(p2)
        assert p1.within(p2, Coord.fromD(29.99)) == False
        assert p1.within(p2, Coord.fromD(30.01)) == True
