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


from chimera.core.chimeraobject import ChimeraObject

from chimera.util.coord import Coord, CoordUtil
from chimera.util.position import Position

from dateutil import tz

try:
    from coords import AstroDate
except ImportError:

    # FIXME: we still doesn`t have coords on Windows, so fake it.
    class AstroDate:
        def __init__ (self, t):
            pass
        
        jd = 0
        mjd = 0

import ephem

import datetime as dt


__all__ = ['Site']


class Site (ChimeraObject):
    
    __config__ = dict(name       = "UFSC",
                      latitude   = Coord.fromDMS("-23 00 00"),
                      longitude  = Coord.fromDMS(-48.5),
                      altitude   = 20,
                      utc_offset = -3)

    def __init__ (self):
        ChimeraObject.__init__(self)

        self._sun  = ephem.Sun()
        self._moon = ephem.Moon()

    def __main__ (self):
        pass

    def _getEphem(self, date=None):
        site = ephem.Observer()
        site.lat  = self["latitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
        site.long = self["longitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
        site.elev = self['altitude']
        site.date = date or self.ut()
        site.epoch='2000/1/1 00:00:00'
        return site

    def _Date2local (self, Date):
        # convert Date to a non-naive datetime with TZ set to UTC
        time_tuple = Date.tuple()
        time_tuple = tuple((int(t) for t in time_tuple))
        time_tuple += (0, self.utc_tz)
        d_utc = dt.datetime(*time_tuple)
        # then return it in local timezone
        return d_utc.astimezone(self.local_tz)
        
    local_tz = property(lambda self: tz.tzoffset(None, self["utc_offset"]*3600))
    utc_tz   = property(lambda self: tz.tzutc())

    def getEphemSite (self, date):
        return self._getEphem(date)

    def JD (self):
        return AstroDate(self.ut()).jd

    def MJD (self):
        # JD - julian date at November 17, 1858 (thanks Sputinik!)
        # http://www.slac.stanford.edu/~rkj/crazytime.txt
        return AstroDate(self.ut()).mjd

    def localtime (self):
        return dt.datetime.now(self.local_tz)

    def ut (self):
        return dt.datetime.now(self.utc_tz)
    
    def LST_inRads(self):
        return float(self._getEphem(date=self.ut()).sidereal_time())

    def LST (self):
        """
        Mean Local Sidereal Time
        """
        #lst = self._getEphem(self.ut()).sidereal_time()
        #required since a Coord cannot be constructed from an Ephem.Angle
        lst_c = Coord.fromR(self.LST_inRads())
        return lst_c.toHMS()

    def GST (self):
        """
        Mean Greenwhich Sidereal Time
        """
        lst = self.LST()
        gst = lst - self["longitude"].toH()
        return gst

    def sunrise (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        return self._Date2local(site.next_rising(self._sun))

    def sunset (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        return self._Date2local(site.next_setting(self._sun))

    def sunset_twilight_begin (self, date=None):
        # http://aa.usno.navy.mil/faq/docs/RST_defs.php
        date = date or self.localtime()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-12:00:00'
        return self._Date2local(site.next_setting(self._sun))

    def sunset_twilight_end (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-18:00:00'
        return self._Date2local(site.next_setting(self._sun))

    def sunrise_twilight_begin (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        site.elev = 0        
        site.horizon = '-18:00:00'
        return self._Date2local(site.next_rising(self._sun))

    def sunrise_twilight_end (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        site.elev = 0        
        site.horizon = '-12:00:00'
        return self._Date2local(site.next_rising(self._sun))

    def sunpos (self, date=None):
        date = date or self.localtime()
        self._sun.compute(self._getEphem(date))

        return Position.fromAltAz(Coord.fromR(self._sun.alt), Coord.fromR(self._sun.az))

    def moonrise (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        return self._Date2local(site.next_rising(self._moon))
    
    def moonset (self, date=None):
        date = date or self.localtime()
        site = self._getEphem(date)
        return self._Date2local(site.next_setting(self._moon))

    def moonpos (self, date=None):
        date = date or self.localtime()
        self._moon.compute(self._getEphem(date))

        return Position.fromAltAz(Coord.fromR(self._moon.alt), Coord.fromR(self._moon.az))

    def moonphase (self, date=None):
        date = date or self.localtime()
        self._moon.compute(self._getEphem(date))
        return self._moon.phase/100.0
    
    def raToHa(self, ra):
        return CoordUtil.raToHa(ra, self.LST_inRads())

    def haToRa(self, ha):
        return CoordUtil.raToHa(ra, self.LST_inRads())
    
    def raDecToAltAz(self, raDec):
        return Position.raDecToAltAz(raDec, self['latitude'], self.LST_inRads())
    
    def altAzToRaDec(self, altAz):
        return Position.altAzToRaDec(altAz, self['latitude'], self.LST_inRads())#    
