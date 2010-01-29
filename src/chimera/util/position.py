
# to allow use outsise chimera
try:
    from chimera.util.coord import Coord, CoordUtil
except ImportError:
    from coord import Coord, CoordUtil

try:
    from chimera.util.enum  import Enum
except ImportError:
    from enum import Enum

import ephem
from types import StringType


__all__ = ['Position']


Epoch   = Enum("J2000", "B1950", "NOW")
System  = Enum("CELESTIAL", "GALACTIC", "ECLIPTIC", "TOPOCENTRIC")


class PositionOutsideLimitsError (Exception):
    pass


class Position (object):
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
    >>> p = Position.fromRaDec('10:00:00', '20:20:20', epoch=Epoch.J2000)
    >>> p = Position.fromRaDec(10, 20) # assume ra in hours and dec in decimal degress
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
    def fromRaDec (ra, dec, epoch=Epoch.J2000):

        try:
            if type(ra) == StringType:
                ra = Coord.fromHMS(ra)
            elif isinstance(ra, Coord):
                ra = ra.toHMS()
            else:
                try:
                    ra = Coord.fromH(float(ra))
                    ra = ra.toHMS()
                except ValueError:
                    raise ValueError("Invalid RA coordinate type %s. Expected numbers, strings or Coords." % str(type(ra)))

            Position._checkRange(float(ra), 0, 360)

        except ValueError, e:
            raise ValueError("Invalid RA coordinate %s" % str(ra))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid RA range %s. Must be between 0-24 hours or 0-360 deg." % str(ra))

        try:
            if type(dec) == StringType:
                dec = Coord.fromDMS(dec)
            elif isinstance(dec, Coord):
                dec = dec.toDMS()
            else:
                try:
                    dec = Coord.fromD(float(dec))
                    dec = dec.toDMS()
                except ValueError:
                    raise ValueError("Invalid DEC coordinate type %s. Expected numbers, strings or Coords." % str(type(dec)))

            Position._checkRange(float(dec), -90, 360)

        except ValueError, e:
            raise ValueError("Invalid DEC coordinate %s" % str(dec))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid DEC range %s. Must be between 0-360 deg or -90 - +90 deg." % str(dec))

        return Position((ra, dec), system=System.CELESTIAL, epoch=epoch)

    @staticmethod
    def fromAltAz (alt, az):
        try:
            if not isinstance(az, Coord):
                az = Coord.fromDMS(az)
            else:
                az = az.toDMS()

            Position._checkRange(float(az), -180, 360)

        except ValueError, e:
            raise ValueError("Invalid AZ coordinate %s" % str(az))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid AZ range %s. Must be between 0-360 deg or -180 - +180 deg." % str(az))

        try:
            if not isinstance(alt, Coord):
                alt = Coord.fromDMS(alt)
            else:
                alt = alt.toDMS()

            Position._checkRange(float(alt), -90, 180)

        except ValueError, e:
            raise ValueError("Invalid ALT coordinate %s" % str(alt))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid ALT range %s. Must be between 0-180 deg or -90 - +90 deg." % str(alt))

        return Position((alt, az), system=System.TOPOCENTRIC)

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
            else:
                long = long.toDMS()

            Position._checkRange(float(long), -180, 360)

        except ValueError, e:
            raise ValueError("Invalid LONGITUDE coordinate %s" % str(long))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid LONGITUDE range %s. Must be between 0-360 deg or -180 - +180 deg." % str(long))

        try:
            if not isinstance(lat, Coord):
                lat = Coord.fromDMS(lat)
            else:
                lat = lat.toDMS()

            Position._checkRange(float(lat), -90, 180)

        except ValueError, e:
            raise ValueError("Invalid LATITUDE coordinate %s" % str(lat))
        except PositionOutsideLimitsError:
            raise ValueError("Invalid LATITUDE range %s. Must be between 0-180 deg or -90 - +90 deg." % str(lat))

        return (long, lat)

    @staticmethod
    def _checkRange(value, lower, upper):
        # handle -0 problem.
        if abs(value) == 0.0:
            value = abs(value)

        if not (lower <= value <= upper):
            raise PositionOutsideLimitsError("Value must between %s and %s." % (lower, upper))
        return True


    def __init__(self, coords,
                 epoch=Epoch.J2000,
                 system=System.CELESTIAL):

        self._coords = coords
        self.system = str(system).lower()
        self.epoch = Epoch.fromStr(str(epoch).upper())

    def __str__(self):
        """
        @rtype: string
        """
        return "%s %s" % tuple(str(c) for c in self.coords)

    def __repr__(self):
        """
        @rtype: string
        """
        return self.__str__()

    def epochString(self):
        if self.epoch == Epoch.J2000:
            return "J2000.0"
        elif self.epoch == Epoch.B1950:
            return "B1950.0"
        else:
            return "J%.2f" % (2000.0 + (ephem.julian_date() - 2451545.0) / 365.25)

    def __eq__(self, other):
        if isinstance(other, Position):
            return (self._coords == other._coords)
        return False

    def __neq__(self, other):
        return not (self == other)

    # -* conversions -*

    # Coord conversion
    coords = property(lambda self: self._coords)

    def __iter__ (self):
        return self.coords.__iter__()

    ra  = property(lambda self: self._coords[0])
    dec = property(lambda self: self._coords[1])

    alt = property(lambda self: self._coords[0])
    az  = property(lambda self: self._coords[1])

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

    def toEphem(self):
        if str(self.epoch).lower() == str(Epoch.J2000).lower():
            epoch = ephem.J2000
        elif str(self.epoch).lower() == str(Epoch.B1950).lower():
            epoch = ephem.B1950
        else:
            epoch = ephem.now()
            
        return ephem.Equatorial(self.ra.R, self.dec.R, epoch=epoch)

    def precess(self, epoch=Epoch.NOW):
        if str(epoch).lower() == str(Epoch.J2000).lower():
            epoch = ephem.J2000
        elif str(epoch).lower() == str(Epoch.B1950).lower():
            epoch = ephem.B1950
        elif str(epoch).lower() == str(Epoch.NOW).lower():
            epoch = ephem.now()

        j2000 = self.toEphem()
        now = ephem.Equatorial(j2000, epoch=epoch)
        return Position.fromRaDec(Coord.fromR(now.ra), Coord.fromR(now.dec), epoch=Epoch.NOW)

    #
    # great circle distance
    #
    def angsep(self, other):
        """
        Calculate the Great Circle Distance from other.

        @param other: position to calculate distance from.
        @type  other: L{Position}

        @returns: The distance from this point to L{other}.
        @rtype: L{Coord} in degress (convertable, as this is a Coord).
        """
        return Coord.fromR(CoordUtil.gcdist(self.R, other.R)).toD()

    def within(self, other, eps=Coord.fromAS(60)):
        """
        Returns wether L{other} is up to L{eps} units from this
        points. (using great circle distance).

        @param other: Same as in angsep.
        @type  other: L{Position}.

        @param eps: Limit distance.
        @type  eps: L{Coord}.

        @returns: Wether L{other} is within {eps} units from this point.
        @rtype: bool
        """
        return (self.angsep(other) <= eps)
        
    # raDecToAltAz and altAzToRaDec adopted from sidereal.py
    # http://www.nmt.edu/tcc/help/lang/python/examples/sidereal/ims/
                
    @staticmethod
    def raDecToAltAz(raDec, latitude, lst):
        decR = CoordUtil.coordToR(raDec.dec)
        latR = CoordUtil.coordToR(latitude)
        ha = CoordUtil.raToHa(raDec.ra, lst)
        haR = CoordUtil.coordToR(ha)
        
        altR,azR = CoordUtil.coordRotate(decR, latR, haR)
        
        return Position.fromAltAz(Coord.fromR(CoordUtil.makeValid180to180(altR)), Coord.fromR(CoordUtil.makeValid0to360(azR)))
    
    @staticmethod
    def altAzToRaDec(altAz, latitude, lst):
        altR = CoordUtil.coordToR(altAz.alt)
        latR = CoordUtil.coordToR(latitude)
        azR = CoordUtil.coordToR(altAz.az)

        decR, haR = CoordUtil.coordRotate(altR, latR, azR)
        
        ra = CoordUtil.haToRa(haR, lst)
        
        return Position.fromRaDec(CoordUtil.makeValid0to360(ra), CoordUtil.makeValid180to180(decR))
