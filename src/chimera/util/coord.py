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

from chimera.util.enum import Enum
from chimera.core.compat import *


__all__ = ['Coord',
           'CoordUtil']


State = Enum("HMS", "DMS", "D", "H", "R", "AS")


class CoordUtil (object):

    COORD_RE = re.compile('((?P<dd>(?P<sign>[+-]?)[\s]*\d+)[dh]?[\s:]*)?((?P<mm>\d+)[m]?[\s:]*)?((?P<ss>\d+)(?P<msec>\.\d*)?([\ss]*))?')

    @staticmethod
    def epsEqual (a, b, eps=1e-6):
        if (a-b) < eps:
            return True
        else:
            return False

    @staticmethod
    def d2hms (d):
        hhs = d/15.0
        hh = int(hhs)
        mms = (hhs - hh)*60
        mm = int(mms)
        ss = (mms - mm)*60

        if CoordUtil.epsEqual(ss, 60):
            ss = 0
            mm+=1
        
        return (hh, mm, ss)

    @staticmethod
    def d2dms (d):
        dd  = int(d)
        mms = (d-dd) * 60
        mm  = int(mms)
        ss  = (mms - mm) * 60

        sign = 1
        if d < 0: sign *= -1

        return (sign, dd, mm, ss)

    @staticmethod
    def dms2d (dms):

        # float/int case
        if type(dms) in [FloatType, IntType, LongType]:
            return float(dms)

        if type(dms) == StringType:

            # try to match the regular expression
            matches = CoordUtil.COORD_RE.match(dms)

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

                d = abs(dd) + mm/60.0 + (ss+msec)/3600.0

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
        return d*15.0

    @staticmethod
    def hms2str (c):
        return c.strfcoord('%(h)02d:%(m)02d:%(s).2f')

    @staticmethod
    def dms2str (c):
        return c.strfcoord('%(d)02d:%(m)02d:%(s).2f')

    @staticmethod
    def strfcoord (c, format=None):
        """strfcoord acts like sprintf family, allowing arbitrary
        coordinate conversion to str following the given template
        format.

        String template follow standard python % mapping. The
        available components are:

        d[d]: decimal degrees (always with sign)
        m[m]: minutes
        s[s]: seconds (can be float)
        s[h]: hours (always with sign)

        Examples:

        'normal' dms string: format='%(d)02d:%(m)02d:%(s).2f'
        'normal' hms string: format='%(h)02d:%(m)02d:%(s).2f'
        """

        default = None

        if c.state == State.HMS:
            default = '%(h)02d:%(m)02d:%(s).2f'
        else:
            default = '%(d)02d:%(m)02d:%(s).2f'
            
        format = format or default

        sign, d, dm, ds = CoordUtil.d2dms(c.D)
        h, hm, hs = CoordUtil.d2hms(c.D)

        # decide which m/s to use
        m = s = 0
        
        if '(h)' in format or '(hh)' in format:
            m = hm
            s = hs
        else:
            m = dm
            s = ds

        subs = dict(d=d, dd=d,
                    m=abs(m), mm=abs(m),
                    s=abs(s), ss=abs(s),
                    h=h, hh=h)

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

     1. object creation: As there is six different representations,
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

    Internals
    =========

     Coord use a simple state machine to present coordinates in the
     desired representation. Internaly, Coord store coordinates in
     decimal degrees no mather which is the state of the
     object. States matter only when using one of primitive getters,
     string representations or when doing math with Coord objects.

     As Coord use a single internal representation, only conversion
     from/to this one are required. No matter which representation you
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
            other = Coord.fromState(other, self.state)
        return Coord(self.D % other.D, self.state)

    def __rmod__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(other.D % self.D, self.state)

    def __add__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(self.D + other.D, self.state)

    def __radd__ (self, other):
        return self.__add__(other)

    def __sub__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(self.D - other.D, self.state)

    def __rsub__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(other.D - self.D, self.state)

    def __mul__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(self.D * other.D, self.state)

    def __rmul__ (self, other):
        return self.__mul__(other)

    def __div__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(self.D / other.D, self.state)

    def __rdiv__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return Coord(other.D / self.D, self.state)

    def __truediv__ (self, other):
        return self.__div__(other)

    def __rtruediv__ (self, other):
        return self.__rdiv__(other)

    # logic
    def __lt__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D < other.D
        
    def __le__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D <= other.D
        
    def __eq__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D == other.D
        
    def __ne__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D != other.D
        
    def __gt__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D > other.D
        
    def __ge__ (self, other):
        if not isinstance(other, Coord):
            other = Coord.fromState(other, self.state)
        return self.D >= other.D

        

        


        
