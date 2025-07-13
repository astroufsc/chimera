# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import datetime as dt
from dateutil import tz
import ephem
import numpy as np

from chimera.core.chimeraobject import ChimeraObject
from chimera.util.coord import Coord, CoordUtil
from chimera.util.position import Position

__all__ = ["Site"]


# More conversion functions.


def datetime_from_jd(jd):
    """Returns a date corresponding to the given Julian day number."""
    if not isinstance(jd, float):
        raise TypeError(f"{str(jd)} is not a float.")

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

    hh = (jd - np.floor(jd)) * 24.0
    mm = int(np.floor((hh - np.floor(hh)) * 60.0))
    hh = int(np.floor(hh))

    ret = dt.datetime(
        year=100 * b + d - 4800 + m / 10,
        month=m + 3 - 12 * (m // 10),
        day=e + 1 - (153 * m + 2) // 5,
        hour=hh,
        minute=mm,
    )

    return ret


class Site(ChimeraObject):
    __config__ = dict(
        name="UFSC",
        latitude=Coord.from_dms("-23 00 00"),
        longitude=Coord.from_dms(-48.5),
        altitude=20,
        flat_alt=Coord.from_dms(80),
        flat_az=Coord.from_dms(0),
    )

    def __init__(self):
        super().__init__()

        self._sun = ephem.Sun()
        self._moon = ephem.Moon()

    def __main__(self):
        pass

    def _get_ephem(self, date=None):
        site = ephem.Observer()
        site.lat = self["latitude"].strfcoord("%(d)d:%(m)d:%(s).2f")
        site.long = self["longitude"].strfcoord("%(d)d:%(m)d:%(s).2f")
        site.elev = self["altitude"]
        site.date = date or self.ut()
        site.epoch = "2000/1/1 00:00:00"
        return site

    def _date_to_local(self, date):
        # convert date to a non-naive datetime with TZ set to UTC
        time_tuple = date.tuple()
        time_tuple = tuple((int(t) for t in time_tuple))
        time_tuple += (0, self.utc_tz)
        d_utc = dt.datetime(*time_tuple)
        # then return it in local timezone
        return d_utc.astimezone(self.utc_tz)

    local_tz = property(lambda self: tz.tzlocal())
    utc_tz = property(lambda self: tz.tzutc())

    def get_ephem_site(self, date):
        return self._get_ephem(date)

    def jd(self, t=None):
        if not t:
            t = self.ut()
        return ephem.julian_date(t)

    def mjd(self, t=None):
        # JD - julian date at November 17, 1858 (thanks Sputinik!)
        # http://www.slac.stanford.edu/~rkj/crazytime.txt
        if not t:
            t = self.ut()
        return self.jd(t) - 2400000.5

    def localtime(self):
        return dt.datetime.now(self.local_tz)

    def ut(self):
        return dt.datetime.now(self.utc_tz)

    def utc_offset(self):
        offset = self.localtime().utcoffset()
        return (offset.days * 86400 + offset.seconds) / 3600.0

    def lst_in_rads(self, date=None):
        if not date:
            date = self.ut()
        return float(self._get_ephem(date=date).sidereal_time())

    def lst(self, date=None):
        """
        Mean Local Sidereal Time
        """
        # lst = self._get_ephem(self.ut()).sidereal_time()
        # required since a Coord cannot be constructed from an Ephem.Angle
        if not date:
            date = self.ut()
        lst_c = Coord.from_r(self.lst_in_rads(date))
        return lst_c.to_hms()

    def gst(self):
        """
        Mean Greenwich Sidereal Time
        """
        lst = self.lst()
        gst = (lst - self["longitude"].to_h()) % Coord.from_h(24)
        return gst

    def sunrise(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_rising(self._sun))

    def sunset(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_setting(self._sun))

    def sunset_twilight_begin(self, date=None):
        # http://aa.usno.navy.mil/faq/docs/RST_defs.php
        date = date or self.ut()
        site = self._get_ephem(date)
        site.elev = 0
        site.horizon = "-12:00:00"
        return self._date_to_local(site.next_setting(self._sun))

    def sunset_twilight_end(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        site.elev = 0
        site.horizon = "-18:00:00"
        return self._date_to_local(site.next_setting(self._sun))

    def sunrise_twilight_begin(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        site.elev = 0
        site.horizon = "-18:00:00"
        return self._date_to_local(site.next_rising(self._sun))

    def sunrise_twilight_end(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        site.elev = 0
        site.horizon = "-12:00:00"
        return self._date_to_local(site.next_rising(self._sun))

    def sunpos(self, date=None):
        date = date or self.ut()
        self._sun.compute(self._get_ephem(date))

        return Position.from_alt_az(
            Coord.from_r(self._sun.alt), Coord.from_r(self._sun.az)
        )

    def moonrise(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_rising(self._moon))

    def moonset(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_setting(self._moon))

    def moonpos(self, date=None):
        date = date or self.ut()
        self._moon.compute(self._get_ephem(date))

        return Position.from_alt_az(
            Coord.from_r(self._moon.alt), Coord.from_r(self._moon.az)
        )

    def moonphase(self, date=None):
        date = date or self.ut()
        self._moon.compute(self._get_ephem(date))
        return self._moon.phase / 100.0

    def ra_to_ha(self, ra):
        return CoordUtil.ra_to_ha(ra, self.lst_in_rads())

    def ha_to_ra(self, ha):
        return CoordUtil.ra_to_ha(ha, self.lst_in_rads())

    def ra_dec_to_alt_az(self, ra_dec, lst_in_rads=None):
        if not lst_in_rads:
            lst_in_rads = self.lst_in_rads()
        return Position.ra_dec_to_alt_az(ra_dec, self["latitude"], lst_in_rads)

    def alt_az_to_ra_dec(self, alt_az, lst_in_rads=None):
        if not lst_in_rads:
            lst_in_rads = self.lst_in_rads()

        return Position.alt_az_to_ra_dec(alt_az, self["latitude"], lst_in_rads)

    def get_metadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        return [
            ("SITE", self["name"], "Site name (in config)"),
            ("LATITUDE", str(self["latitude"]), "Site latitude"),
            ("LONGITUD", str(self["longitude"]), "Site longitude"),
            ("ALTITUDE", str(self["altitude"]), "Site altitude"),
        ]
