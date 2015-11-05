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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


from chimera.core.chimeraobject import ChimeraObject

from chimera.util.coord import Coord, CoordUtil
from chimera.util.position import Position

from dateutil import tz
import ephem

import datetime as dt

import numpy as np

__all__ = ['Site']

# More conversion functions.


def datetimeFromJD(jd):
    """Returns a date corresponding to the given Julian day number."""
    if not isinstance(jd, float):
        raise TypeError, "%s is not an integer." % str(n)

    n = int(np.floor(jd))
    if jd > np.floor(jd) + 0.5:
        n += 1

    a = n + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153

    jd += 0.5

    hh = (jd - np.floor(jd)) * 24.
    mm = int(np.floor((hh - np.floor(hh)) * 60.))
    hh = int(np.floor(hh))

    ret = dt.datetime(year=100 * b + d - 4800 + m / 10,
                      month=m + 3 - 12 * (m // 10),
                      day=e + 1 - (153 * m + 2) // 5,
                      hour=hh,
                      minute=mm)

    return ret


class Site (ChimeraObject):

    __config__ = dict(name="UFSC",
                      latitude=Coord.fromDMS("-23 00 00"),
                      longitude=Coord.fromDMS(-48.5),
                      altitude=20,
                      flat_alt=Coord.fromDMS(80),
                      flat_az=Coord.fromDMS(0))

    def __init__(self):
        ChimeraObject.__init__(self)

        self._sun = ephem.Sun()
        self._moon = ephem.Moon()

    def __main__(self):
        pass

    def _getEphem(self, date=None):
        site = ephem.Observer()
        site.lat = self["latitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
        site.long = self["longitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
        site.elev = self['altitude']
        site.date = date or self.ut()
        site.epoch = '2000/1/1 00:00:00'
        return site

    def _Date2local(self, Date):
        # convert Date to a non-naive datetime with TZ set to UTC
        time_tuple = Date.tuple()
        time_tuple = tuple((int(t) for t in time_tuple))
        time_tuple += (0, self.utc_tz)
        d_utc = dt.datetime(*time_tuple)
        # then return it in local timezone
        return d_utc.astimezone(self.utc_tz)

    local_tz = property(lambda self: tz.tzlocal())
    utc_tz = property(lambda self: tz.tzutc())

    def getEphemSite(self, date):
        return self._getEphem(date)

    def JD(self, t=None):
        if not t:
            t = self.ut()
        return ephem.julian_date(t)

    def MJD(self, t=None):
        # JD - julian date at November 17, 1858 (thanks Sputinik!)
        # http://www.slac.stanford.edu/~rkj/crazytime.txt
        if not t:
            t = self.ut()
        return self.JD(t) - 2400000.5

    def localtime(self):
        return dt.datetime.now(self.local_tz)

    def ut(self):
        return dt.datetime.now(self.utc_tz)

    def utcoffset(self):
        offset = self.localtime().utcoffset()
        return (offset.days * 86400 + offset.seconds) / 3600.0

    def LST_inRads(self, date=None):
        if not date:
            date = self.ut()
        return float(self._getEphem(date=date).sidereal_time())

    def LST(self, date=None):
        """
        Mean Local Sidereal Time
        """
        # lst = self._getEphem(self.ut()).sidereal_time()
        # required since a Coord cannot be constructed from an Ephem.Angle
        if not date:
            date = self.ut()
        lst_c = Coord.fromR(self.LST_inRads(date))
        return lst_c.toHMS()

    def GST(self):
        """
        Mean Greenwhich Sidereal Time
        """
        lst = self.LST()
        gst = (lst - self["longitude"].toH()) % Coord.fromH(24)
        return gst

    def sunrise(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        return self._Date2local(site.next_rising(self._sun))

    def sunset(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        return self._Date2local(site.next_setting(self._sun))

    def sunset_twilight_begin(self, date=None):
        # http://aa.usno.navy.mil/faq/docs/RST_defs.php
        date = date or self.ut()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-12:00:00'
        return self._Date2local(site.next_setting(self._sun))

    def sunset_twilight_end(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-18:00:00'
        return self._Date2local(site.next_setting(self._sun))

    def sunrise_twilight_begin(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-18:00:00'
        return self._Date2local(site.next_rising(self._sun))

    def sunrise_twilight_end(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        site.elev = 0
        site.horizon = '-12:00:00'
        return self._Date2local(site.next_rising(self._sun))

    def sunpos(self, date=None):
        date = date or self.ut()
        self._sun.compute(self._getEphem(date))

        return Position.fromAltAz(
            Coord.fromR(self._sun.alt), Coord.fromR(self._sun.az))

    def moonrise(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        return self._Date2local(site.next_rising(self._moon))

    def moonset(self, date=None):
        date = date or self.ut()
        site = self._getEphem(date)
        return self._Date2local(site.next_setting(self._moon))

    def moonpos(self, date=None):
        date = date or self.ut()
        self._moon.compute(self._getEphem(date))

        return Position.fromAltAz(
            Coord.fromR(self._moon.alt), Coord.fromR(self._moon.az))

    def moonphase(self, date=None):
        date = date or self.ut()
        self._moon.compute(self._getEphem(date))
        return self._moon.phase / 100.0

    def raToHa(self, ra):
        return CoordUtil.raToHa(ra, self.LST_inRads())

    def haToRa(self, ha):
        return CoordUtil.raToHa(ha, self.LST_inRads())

    def raDecToAltAz(self, raDec, lst_inRads=None):
        if not lst_inRads:
            lst_inRads = self.LST_inRads()
        return Position.raDecToAltAz(raDec, self['latitude'], lst_inRads)

    def altAzToRaDec(self, altAz, lst_inRads=None):
        if not lst_inRads:
            lst_inRads = self.LST_inRads()

        return Position.altAzToRaDec(altAz, self['latitude'], lst_inRads)

    def getMetadata(self, request):
        return [
            ('SITE', self['name'], 'Site name (in config)'),
            ('LATITUDE', str(self['latitude']), 'Site latitude'),
            ('LONGITUD', str(self['longitude']), 'Site longitude'),
            ('ALTITUDE', str(self['altitude']), 'Site altitude'),
        ]
