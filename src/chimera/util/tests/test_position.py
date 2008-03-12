

from nose.tools import assert_raises

from chimera.util.position import Position


class TestPosition (object):

    def test_ra_dec (self):

        p = Position.fromRaDec("10:00:00", "20 00 00")
        assert p.dd() == (150, 20)

        assert_raises(ValueError, Position.fromRaDec, "xyz", "abc")

    def test_az_alt (self):

        p = Position.fromAzAlt("200", "60")
        assert p.dd() == (200, 60)

        assert_raises(ValueError, Position.fromAzAlt, "xyz", "abc")        

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

        

        
