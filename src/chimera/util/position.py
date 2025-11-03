# to allow use outsise chimera
try:
    from chimera.util.coord import Coord, CoordUtil
except ImportError:
    from .coord import Coord, CoordUtil

try:
    from chimera.util.enum import Enum
except ImportError:
    from .enum import Enum

import ephem

__all__ = ["Position"]


class Epoch(Enum):
    J2000 = "J2000"
    B1950 = "B1950"
    NOW = "NOW"


class System(Enum):
    CELESTIAL = "CELESTIAL"
    GALACTIC = "GALACTIC"
    ECLIPTIC = "ECLIPTIC"
    TOPOCENTRIC = "TOPOCENTRIC"


class PositionOutsideLimitsError(Exception):
    pass


class Position:
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
    >>> p = Position.from_ra_dec('10:00:00', '20:20:20', epoch=Epoch.J2000)
    >>> p = Position.from_ra_dec(10, 20) # assume ra in hours and dec in decimal degress
    >>> # don't want assumptions? ok, give me a real Coord
    >>> # ok, If you want ra in radians and dec in hours (very strange), use:
    >>> p = Position.from_ra_dec(Coord.from_r(pi), Coord.from_h(10))

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

    >>> p = Position.from_ra_dec('10 00 00', '20 00 00')
    >>> print 'position ra:', p.ra.HMS

    @group Factories: from*
    @group Tuple getters: dd, rad, D, H, R, AS
    @group Coordinate getters: ra, dec, az, alt, long, lat
    """

    @staticmethod
    def from_ra_dec(ra, dec, epoch=Epoch.J2000):

        try:
            if isinstance(ra, str):
                ra = Coord.from_hms(ra)
            elif isinstance(ra, Coord):
                ra = ra.to_hms()
            else:
                try:
                    ra = Coord.from_h(float(ra))
                    ra = ra.to_hms()
                except ValueError:
                    raise ValueError(
                        f"Invalid RA coordinate type {str(type(ra))}. Expected numbers, strings or Coords."
                    )

            Position._check_range(float(ra), 0, 360)

        except ValueError:
            raise ValueError(f"Invalid RA coordinate {str(ra)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid RA range {str(ra)}. Must be between 0-24 hours or 0-360 deg."
            )

        try:
            if isinstance(dec, str):
                dec = Coord.from_dms(dec)
            elif isinstance(dec, Coord):
                dec = dec.to_dms()
            else:
                try:
                    dec = Coord.from_d(float(dec))
                    dec = dec.to_dms()
                except ValueError:
                    raise ValueError(
                        f"Invalid DEC coordinate type {str(type(dec))}. Expected numbers, strings or Coords."
                    )

            Position._check_range(float(dec), -90, 360)

        except ValueError:
            raise ValueError(f"Invalid DEC coordinate {str(dec)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid DEC range {str(dec)}. Must be between 0-360 deg or -90 - +90 deg."
            )

        return Position((ra, dec), system=System.CELESTIAL, epoch=epoch)

    @staticmethod
    def from_alt_az(alt, az):
        try:
            if not isinstance(az, Coord):
                az = Coord.from_dms(az)
            else:
                az = az.to_dms()

            Position._check_range(float(az), -180, 360)

        except ValueError:
            raise ValueError(f"Invalid AZ coordinate {str(az)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid AZ range {str(az)}. Must be between 0-360 deg or -180 - +180 deg."
            )

        try:
            if not isinstance(alt, Coord):
                alt = Coord.from_dms(alt)
            else:
                alt = alt.to_dms()

            Position._check_range(float(alt), -90, 180)

        except ValueError:
            raise ValueError(f"Invalid ALT coordinate {str(alt)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid ALT range {str(alt)}. Must be between 0-180 deg or -90 - +90 deg."
            )

        return Position((alt, az), system=System.TOPOCENTRIC)

    @staticmethod
    def from_long_lat(long, lat):
        return Position(
            Position._generic_long_lat(long, lat), system=System.TOPOCENTRIC
        )

    @staticmethod
    def from_galactic(long, lat):
        return Position(Position._generic_long_lat(long, lat), system=System.GALACTIC)

    @staticmethod
    def from_ecliptic(long, lat):
        return Position(Position._generic_long_lat(long, lat), system=System.ECLIPTIC)

    @staticmethod
    def _generic_long_lat(long, lat):
        try:
            if not isinstance(long, Coord):
                long = Coord.from_dms(long)
            else:
                long = long.to_dms()

            Position._check_range(float(long), -180, 360)

        except ValueError:
            raise ValueError(f"Invalid LONGITUDE coordinate {str(long)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid LONGITUDE range {str(long)}. Must be between 0-360 deg or -180 - +180 deg."
            )

        try:
            if not isinstance(lat, Coord):
                lat = Coord.from_dms(lat)
            else:
                lat = lat.to_dms()

            Position._check_range(float(lat), -90, 180)

        except ValueError:
            raise ValueError(f"Invalid LATITUDE coordinate {str(lat)}")
        except PositionOutsideLimitsError:
            raise ValueError(
                f"Invalid LATITUDE range {str(lat)}. Must be between 0-180 deg or -90 - +90 deg."
            )

        return (long, lat)

    @staticmethod
    def _check_range(value, lower, upper):
        # handle -0 problem.
        if abs(value) == 0.0:
            value = abs(value)

        if not (lower <= value <= upper):
            raise PositionOutsideLimitsError(f"Value must between {lower} and {upper}.")
        return True

    def __init__(self, coords, epoch=Epoch.J2000, system=System.CELESTIAL):

        self._coords = coords
        self.system = System[str(system)]
        self.epoch = Epoch[str(epoch)]

    #
    # serialization
    #
    def __getstate__(self):
        return {
            "_coords": self._coords,
            "system": str(self.system),
            "epoch": str(self.epoch),
        }

    def __setstate__(self, state):
        self._coords = state["_coords"]
        self.system = System[state["system"]]
        self.epoch = Epoch[state["epoch"]]

    def __str__(self):
        """
        @rtype: string
        """
        return "{} {}".format(*tuple(str(c) for c in self.coords))

    # def __repr__(self):
    #     """
    #     @rtype: string
    #     """
    #     return self.__str__()

    def epoch_string(self):
        if self.epoch == Epoch.J2000:
            return "J2000.0"
        elif self.epoch == Epoch.B1950:
            return "B1950.0"
        else:
            return "J%.2f" % (2000.0 + (ephem.julian_date() - 2451545.0) / 365.25)

    def __eq__(self, other):
        if isinstance(other, Position):
            return self._coords == other._coords
        return False

    def __neq__(self, other):
        return not (self == other)

    # -* conversions -*

    # Coord conversion
    coords = property(lambda self: self._coords)

    def __iter__(self):
        return self.coords.__iter__()

    ra = property(lambda self: self._coords[0])
    dec = property(lambda self: self._coords[1])

    alt = property(lambda self: self._coords[0].deg)
    az = property(lambda self: self._coords[1].deg)

    long = property(lambda self: self._coords[0])
    lat = property(lambda self: self._coords[1])

    # primitive conversion
    deg = property(lambda self: tuple(c.deg for c in self.coords))
    radian = property(lambda self: tuple(c.radian for c in self.coords))
    arcsec = property(lambda self: tuple(c.arcsec for c in self.coords))
    hour = property(lambda self: tuple(c.hour for c in self.coords))

    def dd(self):
        return self.deg

    def rad(self):
        return self.radian

    def to_ephem(self):
        if str(self.epoch).lower() == str(Epoch.J2000).lower():
            epoch = ephem.J2000
        elif str(self.epoch).lower() == str(Epoch.B1950).lower():
            epoch = ephem.B1950
        else:
            epoch = ephem.now()

        return ephem.Equatorial(self.ra.radian, self.dec.radian, epoch=epoch)

    def to_epoch(self, epoch=Epoch.J2000):
        """
        Returns a new Coordinate with the specified Epoch
        """

        # If coordinate epoch is already the right one, do nothing
        if str(epoch).lower() == str(self.epoch).lower():
            return self

        # Else, do the coordinate conversion...
        if str(epoch).lower() == str(Epoch.J2000).lower():
            eph_epoch = ephem.J2000
        elif str(epoch).lower() == str(Epoch.B1950).lower():
            eph_epoch = ephem.B1950
        elif str(epoch).lower() == str(Epoch.NOW).lower():
            eph_epoch = ephem.now()

        coords = ephem.Equatorial(self.to_ephem(), epoch=eph_epoch)

        return Position.from_ra_dec(
            Coord.from_r(coords.ra), Coord.from_r(coords.dec), epoch=epoch
        )

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
        return Coord.from_r(CoordUtil.gcdist(self.radian, other.radian)).to_d()

    def within(self, other, eps=Coord.from_as(60)):
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
        return self.angsep(other) <= eps

    # ra_dec_to_alt_az and alt_az_to_ra_dec adopted from sidereal.py
    # http://www.nmt.edu/tcc/help/lang/python/examples/sidereal/ims/

    @staticmethod
    def ra_dec_to_alt_az(ra: float, dec: float, latitude: float, lst: float | None) -> tuple[float, float]:
        # ra in hours, dec in degrees, lat in degrees, lst in radians
        # returns alt, az in degrees
        dec_r = CoordUtil.coord_to_r(Coord.from_d(dec))
        lat_r = CoordUtil.coord_to_r(Coord.from_d(latitude))
        ha = CoordUtil.ra_to_ha(Coord.from_h(ra), Coord.from_r(lst))
        ha_r = CoordUtil.coord_to_r(ha)

        alt_r, az_r = CoordUtil.coord_rotate(dec_r, lat_r, ha_r)

        return float(Coord.from_r(CoordUtil.make_valid_180_to_180(alt_r)).to_d()), float(Coord.from_r(CoordUtil.make_valid_0_to_360(az_r)).to_d())

    @staticmethod
    def alt_az_to_ra_dec(alt: float, az: float, latitude: float, lst: float | None) -> tuple[float, float]:
        # alt, az, lat in degrees, lst in radians
        # returns ra in hours, dec in degrees
        alt_r = CoordUtil.coord_to_r(Coord.from_d(alt))
        lat_r = CoordUtil.coord_to_r(Coord.from_d(latitude))
        az_r = CoordUtil.coord_to_r(Coord.from_d(az))

        dec_r, ha_r = CoordUtil.coord_rotate(alt_r, lat_r, az_r)

        ra = CoordUtil.ha_to_ra(ha_r, lst)

        return float(CoordUtil.make_valid_0_to_360(ra).to_h()), float(CoordUtil.make_valid_180_to_180(dec_r).to_d())
