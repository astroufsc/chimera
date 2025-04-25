# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import math
import re

TWO_PI = 2.0 * math.pi
PI_OVER_TWO = math.pi / 2.0


# to allow use of Coord outside of Chimera

try:
    from chimera.util.enum import Enum
except ImportError:
    from .enum import Enum

__all__ = ["Coord", "CoordUtil"]


class State(Enum):
    HMS = "HMS"
    DMS = "DMS"
    D = "D"
    H = "H"
    R = "R"
    AS = "AS"


class CoordUtil(object):

    COORD_RE = re.compile(
        r"((?P<dd>(?P<sign>[+-]?)[\s]*\d+)[dh]?[\s:]*)?((?P<mm>\d+)[m]?[\s:]*)?((?P<ss>\d+)(?P<msec>\.\d*)?([\ss]*))?"
    )

    _arcsec_to_deg = 1.0 / 3600
    _min_to_deg = 1.0 / 60

    @staticmethod
    def eps_equal(a, b, eps=1e-7):
        return abs(a - b) <= eps

    @staticmethod
    def d_to_hms(d, sec_prec=None):
        """
        See CoordUtil.d_to_dms.
        """
        return CoordUtil.d_to_dms(d / 15, sec_prec)

    @staticmethod
    def d_to_dms(d, sec_prec=None):
        """
        This function returns a tuple which can be used to reconstruct
        the decimal value of Coord as follow:

         d = sign * (dd + mm/60.0 + ss/3600.0)

        sec_prec parameters defines how much decimal places we want on
        seconds values. strfcoord uses this to round values when using
        specific %.xf values.
        """
        dd = int(d)
        mms = (d - dd) * 60
        mm = int(mms)
        ss = (mms - mm) * 60

        # precision defined here
        sec_prec = sec_prec or 7

        # use one decimal place more to don't truncate values when printing,
        # see below.
        sec_prec += 1

        ss = round(ss, sec_prec)

        # eps_equal use one decimal place more to round up if
        # needed, for example: if sec_prec=2, 59.999 with eps=1e-2 ==
        # 60.00, but with eps=1-3 == 59.99 which is what user is
        # expecting.
        if CoordUtil.eps_equal(abs(ss), 60.0, 10 ** (-sec_prec)):
            ss = 0
            if d < 0:
                mm -= 1
            else:
                mm += 1

        sign = 1
        if d < 0:
            sign *= -1

        return (sign, abs(dd), abs(mm), abs(ss))

    @staticmethod
    def dms_to_d(dms):

        # float/int case
        if isinstance(dms, (int, float)):
            return float(dms)

        if isinstance(dms, str):

            # try to match the regular expression
            matches = CoordUtil.COORD_RE.match(dms.strip())

            # our regular expression is tooo general, we need to make sure that things
            # like "xyz" (which is valid) but is a zero-lenght match wont pass
            # silently
            if any(matches.groups()):
                m_dict = matches.groupdict()
                sign = m_dict["sign"] or "+"
                dd = m_dict["dd"] or 0
                mm = m_dict["mm"] or 0
                ss = m_dict["ss"] or 0
                msec = m_dict["msec"] or 0

                try:
                    dd = int(dd)
                    mm = int(mm)
                    ss = int(ss)
                    msec = float(msec)
                except ValueError as e:
                    raise ValueError(f"Invalid coordinate: '{dms}' ({e}).")

                d = (
                    abs(dd)
                    + mm * CoordUtil._min_to_deg
                    + ((ss + msec) * CoordUtil._arcsec_to_deg)
                )

                if sign == "-":
                    d *= -1

                return d

            else:
                # brute force float conversion
                try:
                    return float(dms)
                except ValueError as e:
                    raise ValueError(f"Invalid coordinate: '{dms}' ({e}).")

        raise ValueError(
            f"Invalid coordinate type: '{str(type(dms))}'. Expecting string or numbers."
        )

    @staticmethod
    def hms_to_d(hms):
        d = CoordUtil.dms_to_d(hms)
        return d * 15

    @staticmethod
    def hms_to_str(c):
        return c.strfcoord()

    @staticmethod
    def dms_to_str(c):
        return c.strfcoord()

    @staticmethod
    def strfcoord(c, format=None, signed=True):
        """
        strfcoord acts like sprintf family, allowing arbitrary
        coordinate conversion to str following the given template
        format.

        String template follow standard python % mapping. The
        available components are:

        d[d]: decimal degrees
        m[m]: minutes
        s[s]: seconds (can be float)
        s[h]: hours

        if signed was True, decimal degrees will always begins with
        a sign (+ or -) and hours values will have a negative sign if
        needed. Note that

        Examples:

        'normal' dms string: format='%(d)02d:%(m)02d:%(s)06.3f'
        'normal' hms string: format='%(h)02d:%(m)02d:%(s)06.3f'

        @note: You don't need to add + to your format strings, sign
        will be added as specified above.

        @note: To avoid truncation errors with miliseconds numbers,
        always use %f to represent seconds of arc, This example show
        what can happen if you don't do that:

         >>> c = Coord.from_dms('+13 23 46')
         >>> c
         <Coord object +13:23:46.000 (DMS) at 0x83a3ae>
         >>> print c
         +13:23:46.000
         >>> c.strfcoord('%(d)02d %(m)02d %(s)02d')
         '+13 23 45'
         >>> c.DMS
         (1, 13, 23, 45.999999999999091)
         >>> # the last line show what happened:
         >>> #  %d just truncate while %f rounds the seconds to get the 'right' number
        """

        default = None

        if c.state == State.HMS:
            default = "%(h)02d:%(m)02d:%(s)06.3f"
        else:
            default = "%(d)02d:%(m)02d:%(s)06.3f"

        format = format or default

        # find required precision on seconds
        need = None
        if "%(s)" in format:
            need = "%(s)"
        if "%(ss)" in format:
            need = "%(ss)"

        sec_prec = None

        if need:
            try:
                ss_index = format.index(need)
                sec_prec = format[ss_index : format.index("f", ss_index)]
                parts = sec_prec.split(".")

                if len(parts) == 2:
                    sec_prec = int(parts[1]) + 1
            except ValueError:
                # got a %d or something not like a float
                pass

        sign, d, dm, ds = CoordUtil.d_to_dms(c.deg, sec_prec)
        _, h, hm, hs = CoordUtil.d_to_hms(c.deg, sec_prec)

        # decide about m/s and sign
        # FIXME: strange way to handle -0 cases
        m = s = 0
        sign_str = ""

        if sign < 0:
            sign_str = "-"
        else:
            sign_str = "+"

        if "(h)" in format or "(hh)" in format:
            m = hm
            s = hs
            if sign > 0:
                sign_str = ""
        else:
            m = dm
            s = ds

        subs = dict(d=d, dd=d, m=m, mm=m, s=s, ss=s, h=h, hh=h)

        if signed:
            return (sign_str + format) % subs
        else:
            return format % subs

    @staticmethod
    def coord_to_r(coord):
        if isinstance(coord, Coord):
            return float(coord.to_r())
        else:
            return float(coord)

    @staticmethod
    def make_valid_0_to_360(coord):
        coord_r = CoordUtil.coord_to_r(coord)
        coord_r = coord_r % TWO_PI
        if coord_r < 0.0:
            coord_r += TWO_PI
        return Coord.from_r(coord_r)

    @staticmethod
    def make_valid_180_to_180(coord):
        coord_r = CoordUtil.coord_to_r(coord)
        coord_r = coord_r % TWO_PI
        if coord_r > math.pi:
            coord_r -= TWO_PI
        if coord_r < (-math.pi):
            coord_r += TWO_PI
        return Coord.from_r(coord_r)

    @staticmethod
    def ra_to_ha(ra, lst):
        return Coord.from_r(CoordUtil.coord_to_r(lst) - CoordUtil.coord_to_r(ra))

    @staticmethod
    def ha_to_ra(ha, lst):
        return Coord.from_r(CoordUtil.coord_to_r(lst) - CoordUtil.coord_to_r(ha))

    # coord_rotate adopted from sidereal.py
    # http://www.nmt.edu/tcc/help/lang/python/examples/sidereal/ims/

    @staticmethod
    def coord_rotate(x, y, z):
        """
        Used to convert between equatorial and horizon coordinates.

          [ x, y, and z are angles in radians ->
              return (xt, yt) where
              xt=arcsin(sin(x)*sin(y)+cos(x)*cos(y)*cos(z)) and
              yt=arccos((sin(x)-sin(y)*sin(xt))/(cos(y)*cos(xt))) ]
        """
        # -- 1 --
        xt = math.asin(
            math.sin(x) * math.sin(y) + math.cos(x) * math.cos(y) * math.cos(z)
        )
        # -- 2 --
        yt = math.acos(
            (math.sin(x) - math.sin(y) * math.sin(xt)) / (math.cos(y) * math.cos(xt))
        )
        # -- 3 --
        if math.sin(z) > 0.0:
            yt = TWO_PI - yt

        # -- 4 --
        return (xt, yt)

    # Great circle distance formulae:
    # source http://wiki.astrogrid.org/bin/view/Astrogrid/CelestialCoordinates

    @staticmethod
    def hav(theta):
        """
        have rsine function, units = radians. Used in calculation of great
        circle distance

        @param theta: angle in radians
        @type theta: number

        @rtype: number
        """
        ans = (math.sin(0.5 * theta)) ** 2
        return ans

    @staticmethod
    def ahav(x):
        """
        archaversine function, units = radians. Used in calculation of great
        circle distance

        @type x: number

        @return: angle in radians
        @rtype: number
        """
        ans = 2.0 * math.asin(math.sqrt(x))
        return ans

    @staticmethod
    def gcdist(vec1, vec2):
        """
        Input (ra,dec) vectors in radians;
        output great circle distance in radians.

        @param vec1,vec2: position in radians
        @type vec1: number
        @type vec2: number

        @rtype: great circle distance in radians

        @see: U{http://wiki.astrogrid.org/bin/view/Astrogrid/CelestialCoordinates}
        """
        ra1, dec1 = vec1
        ra2, dec2 = vec2
        ans = CoordUtil.ahav(
            CoordUtil.hav(dec1 - dec2)
            + math.cos(dec1) * math.cos(dec2) * CoordUtil.hav(ra1 - ra2)
        )
        return ans


class Coord(object):
    """
    L{Coord} represents a single angular coordinate.

    It support all the common angle representations found in
    astronomy. This class is intended to be used as part of low level
    manipulations (like in drivers). User wanting high level support
    (like distance computations, reference frames conversions) should
    use L{Position}.

    Supported representations and their associated data types::

     r (radian): float
     h (decimal hours): float
     d (decimal degrees): float
     dms (sexagesimal degrees) -> (sign: int, degrees: int, minutes: int, seconds: float) tuple
     hms (sexagesimal hours) -> (hours: int, minutes: int, seconds: float) -> tuple
     as (arc seconds): float


    This class have very particular semantics:

     0. This class is immutable, in other words, every operation that
     need to change this object will return a new one.

     1. object creation: There are six different representations, so,
     instead of remember how parameters should be passed to __init__
     constructor, use Coord.from* forms to leave your code away of
     low-level code when creating Coord objects. from* acts like
     factories of Coords.

     2. primitive conversions: to get primitive data (like int, long,
     float or tuples) from Coord use the attribute access (D, HMS,
     DMS, and so on). This returns a primitive value, that can't be
     converted back to another representation (at least not directly
     as when using to* forms).

      2.1. Another way to get a primitive value is using Python's
      standard factories (int, float, tuple). Coord convert itself to
      required factory type.

     3. object conversions: To get a copy of the Coord using another
     representation, use to* factories. This will return a new
     instance of Coord, using the given representation. This is useful
     if you need to store different representations of the same
     coordinate independently of each other and express this intent
     explicitly.

     4. Coord doesn't do any range checking. Its up to Position and
     more higher level classes to do this. As the are no bounds in
     angle values, Coord respect this and don't check for valid ranges.

    Math
    ====

     You can use Coord with most mathematical operators and special
     functions (abs, mod). Note that in a binary operation, if one of
     the operands was not a Coord instance, it will be treated as a
     decimal degrees value, no matter the state of the other (which
     must be a Coord) operand. This make you code more math-readable,
     see an example below. The idea is that 'cause our internal
     representation is decimal degrees, this forms the base unit, so
     to respect math laws like 1*a=a we must use this scheme, see
     belew. To use other representations, just create an appropriate
     one and do the math again.

      >>> c = Coord.fromHMS('10:10:10')
      >>> c
      <Coord object 10:10:10.00 (HMS) at 0xb7804a4c>
      >>> c.deg
      152.54166666666666
      >>> d = 1*c
      >>> d.deg
      152.54166666666666
      >>> # if we interpret 1 as a HMS value, d would be (1H=15D):
      >>> d.deg
      2288.125
      >>> d
      <Coord object 152:33:0.00 (HMS) at 0xb7804cac>

     However, there is a way to bypass this behaviour: if the
     non-Coord operand was a string, then the string will be
     interpreted using the same state as the Coord operand, so code
     likt this would be possible:

     >>> c = Coord.fromHMS('10:10:10')
     >>> d = c+'1:0:0'
     >>> d
     >>> <Coord object 11:10:10.00 (HMS) at 0xb7804a4c>


    Internals
    =========

     Coord use a simple state machine to present coordinates in the
     desired representation. Internaly, Coord store coordinates in
     decimal degrees no mather which is the state of the
     object. States matter only when using one of primitive getters,
     string representations or when doing math with Coord objects.

     As Coord use a single internal representation, only conversion
     from/to this one are required. No matter what representation you
     want, its just one pass to get there. To speed-up most time
     consuming conversions (dms->d, hms-d, and vice versa), and using
     the fact that Coord is immutable, Coord store recent computations
     in a cache and return this version when asked for that
     representation again.

     Only math operations (apart of factories, of course) return new
     Coord objects.
    """

    deg_to_rad = math.pi / 180.0
    rad_to_deg = 180.0 / math.pi

    # internal state conversions from/to internal
    # representation (decimal degrees)
    from_states = {
        State.HMS: CoordUtil.hms_to_d,
        State.DMS: CoordUtil.dms_to_d,
        State.D: lambda d: float(d),
        State.H: lambda h: h * 15.0,
        State.R: lambda r: r * Coord.rad_to_deg,
        State.AS: lambda as_: as_ / 3600.0,
    }

    to_states = {
        State.HMS: CoordUtil.d_to_hms,
        State.DMS: CoordUtil.d_to_dms,
        State.D: lambda d: float(d),
        State.H: lambda d: d / 15.0,
        State.R: lambda d: d * Coord.deg_to_rad,
        State.AS: lambda d: d * 3600.0,
    }

    # DON'T CALL THIS CONSTRUCTOR DIRECTLY, USE from* FORMS
    def __init__(self, v, state):
        self.v = v
        self.state = state
        self.cache = {}

    #
    # serialization
    #
    def __getstate__(self):
        return {"v": self.v, "state": str(self.state)}

    def __setstate__(self, state):
        self.v = state["v"]
        self.state = State[state["state"]]
        self.cache = {}

    #
    # factories
    #

    @staticmethod
    def from_hms(c):
        v = Coord.from_states[State.HMS](c)
        return Coord(v, State.HMS)

    @staticmethod
    def from_dms(c):
        v = Coord.from_states[State.DMS](c)
        return Coord(v, State.DMS)

    @staticmethod
    def from_d(c):
        return Coord._from_float_to(c, State.D)

    @staticmethod
    def from_h(c):
        return Coord._from_float_to(c, State.H)

    @staticmethod
    def from_r(c):
        return Coord._from_float_to(c, State.R)

    @staticmethod
    def from_as(c):
        return Coord._from_float_to(c, State.AS)

    @staticmethod
    def from_state(c, state):
        method_name = f"from_{state.lower()}"
        ctr = getattr(Coord, method_name)
        if hasattr(ctr, "__call__"):
            return ctr(c)
        else:
            raise ValueError("Trying to create Coord " f"from unknown state {state}")

    @staticmethod
    def _from_float_to(c, state):

        if isinstance(c, str):
            try:
                c = float(c)
            except ValueError:
                raise ValueError(f"Invalid coordinate: '{str(c)}'")

        c = Coord.from_states[state](c)
        return Coord(c, state)

    #
    # conversion factories
    #
    def to_hms(self):
        return Coord(self.deg, State.HMS)

    def to_dms(self):
        return Coord(self.deg, State.DMS)

    def to_d(self):
        return Coord(self.deg, State.D)

    def to_h(self):
        return Coord(self.deg, State.H)

    def to_r(self):
        return Coord(self.deg, State.R)

    def to_as(self):
        return Coord(self.deg, State.AS)

    #
    # primitive getters (properties, actually)
    #
    hms = property(lambda self: self.get(State.HMS))
    dms = property(lambda self: self.get(State.DMS))
    deg = property(lambda self: self.get(State.D))
    hour = property(lambda self: self.get(State.H))
    radian = property(lambda self: self.get(State.R))
    arcsec = property(lambda self: self.get(State.AS))

    def get(self, state=None):

        state = state or self.state

        if state in self.cache:
            return self.cache[state]

        v = Coord.to_states[state](self.v)

        # save to cache
        self.cache[state] = v

        return v

    #
    # string conversions
    #

    def __repr__(self):
        return f"<{Coord.__name__} object {str(self)} ({self.state}) at {hex(id(self))[:-1]}>"

    def __str__(self):
        if self.state == State.DMS:
            return CoordUtil.dms_to_str(self)
        elif self.state == State.HMS:
            return CoordUtil.hms_to_str(self)
        else:
            return f"{self.get():.2f}"

    def strfcoord(self, *args, **kwargs):
        return CoordUtil.strfcoord(self, *args, **kwargs)

    #
    # primitive conversion
    #

    def __int__(self):
        if self.state in [State.DMS, State.HMS]:
            return int(self.get(State.D))
        else:
            return int(self.get())

    def __float__(self):
        if self.state in [State.DMS, State.HMS]:
            return float(self.get(State.D))
        else:
            return float(self.get())

    def __iter__(self):
        if self.state in [State.DMS, State.HMS]:
            for v in self.get():
                yield v
        else:
            yield self.get()

    #
    # hash
    #

    def __hash__(self):
        return hash(self.deg)

    #
    # math
    #

    def __neg__(self):
        return Coord(-self.deg, self.state)

    def __pos__(self):
        return Coord(+self.deg, self.state)

    def __abs__(self):
        return Coord(abs(self.deg), self.state)

    def __mod__(self, other):
        if not isinstance(other, Coord):
            other = Coord.from_state(other, State.D)
        return Coord(self.deg % other.deg, self.state)

    def __rmod__(self, other):
        if not isinstance(other, Coord):
            other = Coord.from_state(other, State.D)
        return Coord(other.deg % self.deg, self.state)

    def __add__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(self.deg + other.deg, self.state)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(self.deg - other.deg, self.state)

    def __rsub__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(other.deg - self.deg, self.state)

    def __mul__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(self.deg * other.deg, self.state)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(self.deg / other.deg, self.state)

    def __rdiv__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return Coord(other.deg / self.deg, self.state)

    def __truediv__(self, other):
        return self.__div__(other)

    def __rtruediv__(self, other):
        return self.__rdiv__(other)

    # logic
    def __lt__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return self.deg < other.deg

    def __le__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)

        return self.deg <= other.deg

    def __eq__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return self.deg == other.deg

    def __ne__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return self.deg != other.deg

    def __gt__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return self.deg > other.deg

    def __ge__(self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.from_state(other, self.state)
            else:
                other = Coord.from_state(other, State.D)
        return self.deg >= other.deg
