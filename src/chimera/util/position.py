

from types import StringType, IntType, FloatType, LongType

have_coords = True

try:
    from coords import Position as CoordsPosition
    from coords import astrodate
    from coords import pytpm
except ImportError:
    class CoordsPosition(object): pass
    have_coords = False

# to allow use outsise chimera

try:
    from chimera.util.coord import Coord
except ImportError:
    from coord import Coord

try:
    from chimera.util.enum  import Enum
except ImportError:
    from enum import Enum


__all__ = ['Position']


Equinox = Enum("J2000", "B1950")
Epoch   = Enum("J2000", "B1950", "NOW")
System  = Enum("CELESTIAL", "GALACTIC", "ECLIPTIC", "TOPOCENTRIC")


class PositionOutsideLimitsError (Exception):
    pass


class Position (CoordsPosition):
    """Position represents a coordinate pair in a reference frame.

    There are five factories available, that can be used to create
    Position in different frames.

    Each factory accepts a pair of parameters. The parameters format
    is tied to the choosen frame. The intent is to accept the most
    common form of coordinate pair in each frame. For example, ra/dec
    coordinates are mostly given in 'hms dms' format, so this is the
    default used when strings are passed, however, if integers/floats
    are given, these will be interpreted as 'dd dd' (which is also
    common).

    However, the common sense isn't common to everyone and to allow
    these different point of views, every factory acceps a Coord
    object as well, which can be created from a bunch of different
    representations. See L{Coord} for more information on the
    available representations.

    Examples:

    >>> # assumes ra in hms and declination in dms
    >>> p = Position.fromRaDec('10:00:00', '20:20:20', equinox=Equinox.J2000)
    >>> p = Position.fromRaDec(10, 20) # assume ra and dec in decimal degress
    >>> # don't want assumptions? ok, give me a real Coord
    >>> # ok, If you want ra in radians and dec in hours (very strange), use:
    >>> p = Position.fromRaDec(Coord.fromR(pi), Coord.fromH(10))

    No matter which representation is given, the value will be checked
    for range validity.

    The following ranges are imposed::

      +----------------+------------------------------+
      | Right Ascension| 0-24 hours or 0-360 degrees  |
      | Declination    | -90 - +90 or 0-180 degrees   |
      | Latitude       | -90 - +90 or 0-180 degrees   |
      | Longitude      | -180 - +180 or 0-360 degrees |
      | Azimuth        | -180 - +180 or 0-360 degrees |
      | Altitude       | -90 - +90 or 0-180 degrees   |
      +----------------+------------------------------+


    Position offers a wide range of getters. You can get the
    coordinate itself, a Coord instance, or a primitive (int/float)
    converted from those instances. Also, to allow explicity intention
    and code documentation, Position also offers getter with a short
    name of the respective coordinate pais, like ra for Right
    Ascension and so on. These getter returns a Coord object wich can
    be used to get another representations or conversions.

    >>> p = Position.fromRaDec('10 00 00', '20 00 00')
    >>> print 'position ra:', p.ra.HMS
    
    @group Factories: from*
    @group Tuple getters: dd, rad, D, H, R, AS
    @group Coordinate getters: ra, dec, az, alt, long, lat
    """

    @staticmethod
    def fromRaDec (ra, dec, equinox=Equinox.J2000):

        try:
            if type(ra) in [IntType, LongType, FloatType]:
                ra = Coord.fromD(ra)
            elif type(ra) == StringType:
                ra = Coord.fromHMS(ra)
            elif isinstance(ra, Coord):
                pass
            else:
                raise ValueError("Invalid RA coordinate type %s. Expected numbers, strings or Coords." % str(type(ra)))

            Position._checkRange(float(ra), 0, 360)

        except ValueError, e:
            raise ValueError("Invalid RA coordinate %s (%s)" % (str(ra), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid RA range %s. Must be between 0-24 hours or 0-360 deg." % str(ra))

        try:
            if type(dec) in [IntType, LongType, FloatType]:
                dec = Coord.fromD(dec)
            elif type(dec) == StringType:
                dec = Coord.fromDMS(dec)
            elif isinstance(dec, Coord):
                pass
            else:
                raise ValueError("Invalid DEC coordinate type %s. Expected numbers, strings or Coords." % str(type(dec)))

            Position._checkRange(float(dec), -90, 360)

        except ValueError, e:
            raise ValueError("Invalid DEC coordinate %s (%s)" % (str(dec), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid DEC range %s. Must be between 0-360 deg or -90 - +90 deg." % str(dec))

        return Position((ra, dec), system=System.CELESTIAL, equinox=equinox)

    @staticmethod
    def fromAzAlt (az, alt):
        try:
            if not isinstance(az, Coord):
                az = Coord.fromDMS(az)

            Position._checkRange(float(az), -180, 360)

        except ValueError, e:
            raise ValueError("Invalid AZ coordinate %s (%s)" % (str(az), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid AZ range %s. Must be between 0-360 deg or -180 - +180 deg." % str(az))

        try:
            if not isinstance(alt, Coord):
                alt = Coord.fromDMS(alt)

            Position._checkRange(float(alt), -90, 180)

        except ValueError, e:
            raise ValueError("Invalid ALT coordinate %s (%s)" % (str(alt), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid ALT range %s. Must be between 0-180 deg or -90 - +90 deg." % str(alt))

        return Position((az, alt), system=System.TOPOCENTRIC)

    @staticmethod
    def fromLongLat (long, lat):
        return Position(Position._genericLongLat(long, lat), system=System.TOPOCENTRIC)

    @staticmethod
    def fromGalactic (long, lat):
        return Position(Position._genericLongLat(long, lat), system=System.GALACTIC)

    @staticmethod
    def fromEcliptic (long, lat):
        return Position(Position._genericLongLat(long, lat), system=System.ECLIPTIC)

    @staticmethod
    def _genericLongLat (long, lat):
        try:
            if not isinstance(long, Coord):
                long = Coord.fromDMS(long)

            Position._checkRange(float(long), -180, 360)

        except ValueError, e:
            raise ValueError("Invalid LONGITUDE coordinate %s (%s)" % (str(long), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid LONGITUDE range %s. Must be between 0-360 deg or -180 - +180 deg." % str(long))

        try:
            if not isinstance(lat, Coord):
                lat = Coord.fromDMS(lat)

            Position._checkRange(float(lat), -90, 180)

        except ValueError, e:
            raise ValueError("Invalid LATITUDE coordinate %s (%s)" % (str(lat), e))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid LATITUDE range %s. Must be between 0-180 deg or -90 - +90 deg." % str(lat))

        return (long, lat)

    @staticmethod
    def _checkRange(value, lower, upper):
        if not (lower <= value <= upper):
            raise PositionOutsideLimitsError("Value must between %s and %s." % (lower, upper))
        return True


    def __init__(self, coords,
                 equinox=Equinox.J2000,
                 system=System.CELESTIAL):

        self._coords = coords
        self._internal = tuple(float(c.toD()) for c in self.coords)

        self.system = str(system).lower()
        self.units  = 'degrees'

        try:
            self.equinox = str(equinox).lower()
        except:
            self.equinox = equinox #to support arbitrary equinoxes

        if have_coords:
            self._set_tpmstate()

    def __getinitargs__ (self):
        return (self._coords, self.equinox, self.system)

    def _set_tpmstate(self):
        """ Define the state for TPM based on equinox and system """
        if self.system == 'galactic':
            self._tpmstate=4
            self._tpmequinox=astrodate.BesselDate(1958.0).jd
        elif self.system == 'ecliptic':
            self._tpmstate=3
            self._tpmequinox=astrodate.JulianDate(1984.0).jd
        elif self.system == 'celestial':
            if self.equinox == 'j2000':
                self._tpmstate=6
                self._tpmequinox=pytpm.j2000
            elif self.equinox == 'b1950':
                self._tpmstate=5
                self._tpmequinox=pytpm.b1950
            else: #arbitrary equinox. assume FK5 for now, but this is bad.
                self._tpmstate=2
                self._tpmequinox=astrodate.JulianDate(self.equinox).jd
        elif self.system == "topocentric":
            self._tpmstate=19
            self._tpmequinox=pytpm.j2000
        
    def __repr__(self):
        """
        @rtype: string
        """
        return self.__str__()

    def __str__(self):
        """
        @rtype: string
        """
        return "%s %s" % tuple(str(c) for c in self.coords)

    # -* conversions -*


    # Coord conversion
    coords = property(lambda self: self._coords)

    def __tuple__ (self):
        return tuple(self.coords)

    ra  = property(lambda self: self._coords[0])
    dec = property(lambda self: self._coords[1])
    
    az  = property(lambda self: self._coords[0])
    alt = property(lambda self: self._coords[1])

    long = property(lambda self: self._coords[0])
    lat  = property(lambda self: self._coords[1])

    # primitive conversion
    D  = property(lambda self: tuple((c.D  for c in self.coords)))
    R  = property(lambda self: tuple((c.R  for c in self.coords)))
    AS = property(lambda self: tuple((c.AS for c in self.coords)))
    H  = property(lambda self: tuple((c.H  for c in self.coords)))
        
    def dd (self):
        return self.D

    def rad (self):
        return self.R
