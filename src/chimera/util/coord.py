#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import math
import re
import sys
from types import StringType, LongType, IntType, FloatType


# to allow use of Coord outside of Chimera

try:
    from chimera.util.enum import Enum
except ImportError:
    from enum import Enum

try:
    from chimera.core.compat import *
except ImportError:
    if sys.version_info[:2] < (2,5):

        def any (iterable):
            for element in iterable:
                if element: return True
            return False


__all__ = ['Coord',
           'CoordUtil']


State = Enum("HMS", "DMS", "D", "H", "R", "AS")


class CoordUtil (object):

    COORD_RE = re.compile('((?P<dd>(?P<sign>[+-]?)[\s]*\d+)[dh]?[\s:]*)?((?P<mm>\d+)[m]?[\s:]*)?((?P<ss>\d+)(?P<msec>\.\d*)?([\ss]*))?')

    _arcsec2deg = 1.0/3600    
    _min2deg    = 1.0/60

    @staticmethod
    def epsEqual (a, b, eps=1e-7):
        return abs(a-b) <= eps

    @staticmethod
    def d2hms (d, sec_prec=None):
        """
        See CoordUtil.d2dms.
        """
        return CoordUtil.d2dms(d/15, sec_prec)

    @staticmethod
    def d2dms (d, sec_prec=None):
        """
        This function returns a tuple which can be used to reconstruct
        the decimal value of Coord as follow:

         d = sign * (dd + mm/60.0 + ss/3600.0)

        sec_prec parameters defines how much decimal places we want on
        seconds values. strfcoord uses this to round values when using
        specific %.xf values.
        """
        dd  = int(d)
        mms = (d-dd) * 60
        mm  = int(mms)
        ss  = (mms - mm) * 60

        # precision defined here
        sec_prec = sec_prec or 7

        # use one decimal place more to don't truncate values when printing, see below.
        sec_prec += 1

        ss = round(ss, sec_prec)

        # epsEqual use one decimal place more to round up if
        # needed, for example: if sec_prec=2, 59.999 with eps=1e-2 ==
        # 60.00, but with eps=1-3 == 59.99 which is what user is
        # expecting.
        if CoordUtil.epsEqual(abs(ss), 60.0, 10**(-sec_prec)):
            ss  = 0
            if d < 0: mm -= 1
            else:     mm += 1

        sign = 1
        if d < 0:
            sign *= -1

        return (sign, abs(dd), abs(mm), abs(ss))

    @staticmethod
    def dms2d (dms):

        # float/int case
        if type(dms) in [FloatType, IntType, LongType]:
            return float(dms)

        if type(dms) == StringType:

            # try to match the regular expression
            matches = CoordUtil.COORD_RE.match(dms.strip())

            # our regular expression is tooo general, we need to make sure that things
            # like "xyz" (which is valid) but is a zero-lenght match wont pass silently
            if any(matches.groups()):
                m_dict = matches.groupdict()
                sign=m_dict["sign"] or '+'                
                dd = m_dict["dd"] or 0
                mm = m_dict["mm"] or 0
                ss = m_dict["ss"] or 0
                msec = m_dict["msec"] or 0

                try:
                    dd = int(dd)
                    mm = int(mm)
                    ss = int(ss)
                    msec = float(msec)
                except ValueError, e:
                    raise ValueError("Invalid coordinate: '%s' (%s)." % (dms, e))

                d = abs(dd) + mm*CoordUtil._min2deg + ((ss+msec) * CoordUtil._arcsec2deg)

                if sign == '-':
                    d *= -1

                return d
                
            else:
                # brute force float conversion
                try:
                    return float(dms)
                except ValueError, e:
                    raise ValueError("Invalid coordinate: '%s' (%s)." % (dms, e))

        raise ValueError("Invalid coordinate type: '%s'. Expecting string or numbers." % str(type(dms)))

    @staticmethod
    def hms2d (hms):
        d = CoordUtil.dms2d(hms)
        return d*15

    @staticmethod
    def hms2str (c):
        return c.strfcoord()

    @staticmethod
    def dms2str (c):
        return c.strfcoord()

    @staticmethod
    def strfcoord (c, format=None, add_sign=True):
        """strfcoord acts like sprintf family, allowing arbitrary
        coordinate conversion to str following the given template
        format.

        String template follow standard python % mapping. The
        available components are:

        d[d]: decimal degrees
        m[m]: minutes
        s[s]: seconds (can be float)
        s[h]: hours

        if add_sign was True, decimal degrees will always begins with
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

         >>> c = Coord.fromDMS('+13 23 46')
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
            default = '%(h)02d:%(m)02d:%(s)06.3f'
        else:
            default = '%(d)02d:%(m)02d:%(s)06.3f'
            
        format = format or default

        # find required precision on seconds
        need = None
        if "%(s)" in format:
            need = "%(s)"
        if "%(ss)" in format:
            need = "%(ss)"

        sec_prec = None
        
        if need:
            ss_index = format.index(need)
            sec_prec = format[ss_index:format.index('f', ss_index)]
            parts = sec_prec.split(".")
            if len(parts) == 2:
                sec_prec = int(parts[1])+1

        sign, d, dm, ds = CoordUtil.d2dms(c.D, sec_prec)
        _, h, hm, hs = CoordUtil.d2hms(c.D, sec_prec)

        # decide about m/s and sign
        # FIXME: strange way to handle -0 cases
        m = s = 0
        sign_str = ""

        if sign < 0:
            sign_str = "-"
        else:
            sign_str = "+"
        
        if '(h)' in format or '(hh)' in format:
            m = hm
            s = hs
            if sign > 0: sign_str = ""
        else:
            m = dm
            s = ds

        subs = dict(d=d, dd=d,
                    m=m, mm=m,
                    s=s, ss=s,
                    h=h, hh=h)

        if add_sign:
            return (sign_str+format) % subs
        else:
            return format % subs


class Coord (object):
    """L{Coord} represents a single angular coordinate.

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
      >>> c.D
      152.54166666666666
      >>> d = 1*c
      >>> d.D
      152.54166666666666
      >>> # if we interpret 1 as a HMS value, d would be (1H=15D):
      >>> d.D
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

    deg2rad = math.pi/180.0
    rad2deg = 180.0/math.pi

    # internal state conversions from/to internal
    # representation (decimal degrees)
    from_state = {State.HMS: CoordUtil.hms2d,
                  State.DMS: CoordUtil.dms2d,
                  State.D  : lambda d  : float(d),
                  State.H  : lambda h  : h*15.0,
                  State.R  : lambda r  : r * Coord.rad2deg,
                  State.AS : lambda as : as/3600.0}
    
    to_state = {State.HMS: CoordUtil.d2hms, 
                State.DMS: CoordUtil.d2dms,
                State.D  : lambda d: float(d),
                State.H  : lambda d: d/15.0,
                State.R  : lambda d: d*Coord.deg2rad,
                State.AS : lambda d: d*3600.0}


    # DON'T CALL THIS CONSTRUCTOR DIRECTLY, USE from* FORMS
    def __init__ (self, v, state):
        self.v = v
        self.state = state
        self.cache = {}

    #
    # factories
    #

    @staticmethod
    def fromHMS (c):
        v = Coord.from_state[State.HMS](c)
        return Coord(v, State.HMS)

    @staticmethod
    def fromDMS (c):
        v = Coord.from_state[State.DMS](c)
        return Coord(v, State.DMS)

    @staticmethod
    def fromD (c):
        return Coord._from_float_to(c, State.D)

    @staticmethod
    def fromH (c):
        return Coord._from_float_to(c, State.H)

    @staticmethod
    def fromR (c):
        return Coord._from_float_to(c, State.R)

    @staticmethod
    def fromAS (c):
        return Coord._from_float_to(c, State.AS)

    @staticmethod
    def fromState (c, state):
        ctr = getattr(Coord, 'from%s' % state)
        if hasattr(ctr, '__call__'):
            return ctr(c)
        else:
            raise ValueError("Trying to create Coord "
                             "from unknown state %s" % state)

    @staticmethod
    def _from_float_to (c, state):

        if type(c) == StringType:
            try:
                c = float(c)
            except ValueError:
                raise ValueError("Invalid coordinate: '%s'" % str(c))

        c = Coord.from_state[state](c)
        return Coord(c, state)


    #
    # conversion factories
    #

    def toHMS (self):
        return Coord(self.D, State.HMS)

    def toDMS (self):
        return Coord(self.D, State.DMS)

    def toD (self):
        return Coord(self.D, State.D)

    def toH (self):
        return Coord(self.D, State.H)

    def toR (self):
        return Coord(self.D, State.R)

    def toAS (self):
        return Coord(self.D, State.AS)


    #
    # primitive getters (properties, actually)
    #

    HMS = property(lambda self: self.get(State.HMS))
    DMS = property(lambda self: self.get(State.DMS))
    D   = property(lambda self: self.get(State.D))
    H   = property(lambda self: self.get(State.H))
    R   = property(lambda self: self.get(State.R))
    AS  = property(lambda self: self.get(State.AS))

    def get (self, state=None):

        state = state or self.state

        if state in self.cache:
            return self.cache[state]

        v = Coord.to_state[state](self.v)

        # save to cache
        self.cache[state] = v

        return v

    #
    # string conversions
    #

    def __repr__ (self):
        return '<%s object %s (%s) at %s>' % (Coord.__name__, str(self),
                                              self.state, hex(id(self))[:-1])

    def __str__ (self):
        if self.state == State.DMS:
            return CoordUtil.dms2str(self)
        elif self.state == State.HMS:
            return CoordUtil.hms2str(self)
        else:
            return '%.2f' % self.get()

    def strfcoord (self, format=None):
        return CoordUtil.strfcoord(self, format)

    #
    # primitive conversion
    #

    def __int__ (self):
        if self.state in [State.DMS, State.HMS]:
            return int(self.get(State.D))
        else:
            return int(self.get())

    def __float__ (self):
        if self.state in [State.DMS, State.HMS]:
            return float(self.get(State.D))
        else:
            return float(self.get())

    def __iter__ (self):
        if self.state in [State.DMS, State.HMS]:
            for v in self.get():
                yield v
        else:
            yield self.get()

    #
    # hash
    #

    def __hash__ (self):
        return hash(self.D)

    #
    # math
    #

    def __neg__ (self):
        return Coord(-self.D, self.state)

    def __pos__ (self):
        return Coord(+self.D, self.state)

    def __abs__ (self):
        return Coord(abs(self.D), self.state)

    def __mod__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, State.D)
        return Coord(self.D % other.D, self.state)

    def __rmod__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, State.D)
        return Coord(other.D % self.D, self.state)

    def __add__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(self.D + other.D, self.state)

    def __radd__ (self, other):
        return self.__add__(other)

    def __sub__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(self.D - other.D, self.state)

    def __rsub__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(other.D - self.D, self.state)

    def __mul__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(self.D * other.D, self.state)

    def __rmul__ (self, other):
        return self.__mul__(other)

    def __div__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(self.D / other.D, self.state)

    def __rdiv__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return Coord(other.D / self.D, self.state)

    def __truediv__ (self, other):
        return self.__div__(other)

    def __rtruediv__ (self, other):
        return self.__rdiv__(other)

    # logic
    def __lt__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D < other.D

    def __le__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D <= other.D

    def __eq__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D == other.D

    def __ne__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D != other.D

    def __gt__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D > other.D

    def __ge__ (self, other):
        if not isinstance(other, Coord):
            if isinstance(other, str):
                other = Coord.fromState(other, self.state)
            else:
                other = Coord.fromState(other, State.D)
        return self.D >= other.D







