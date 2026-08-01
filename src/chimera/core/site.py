# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import datetime as dt
import threading

import ephem
from dateutil import tz

from chimera.core.chimeraobject import ChimeraObject
from chimera.util.coord import Coord, CoordUtil
from chimera.util.position import Position

__all__ = ["Site"]


class Site(ChimeraObject):
    """
    Site-related information: coordinates, clocks (including the
    fast-forward simulation clock), sidereal time and sun/moon ephemeris.

    A single instance is shared in-process by every managed object through
    ChimeraObject.get_site(), so its methods are called concurrently from
    many threads. Config access is rwlock-guarded; the shared ephem state
    is NOT (see the NOTEs below).
    """

    __config__ = dict(
        name="UFSC",
        latitude=Coord.from_dms("-23 00 00"),
        longitude=Coord.from_dms(-48.5),
        altitude=20,
        flat_alt=Coord.from_dms(80),
        flat_az=Coord.from_dms(0),
        # Fast-forward (simulation) clock, OFF by default.  When
        # time_speedup != 1 or time_start is set, ut() runs a scaled clock:
        #   ut() = time_start + (wall_now - wall_at_first_call) * time_speedup
        # so the whole observatory (scheduler, robobs, sky flats, FITS
        # timestamps) advances through a night in compressed real time.
        # time_start is an ISO/"YYYY-MM-DD HH:MM:SS" UT instant; empty means
        # "start now" (pure speedup with no jump).
        time_speedup=1.0,
        time_start="",
    )

    def __init__(self):
        super().__init__()

        # NOTE(thread-safety): shared mutable pyephem bodies. compute() and
        # next_rising/next_setting() mutate them in place, so concurrent
        # calls to the sun/moon methods race on these objects.
        self._sun = ephem.Sun()
        self._moon = ephem.Moon()

        # fast-forward clock anchors, captured on the first ut() call
        self._ff_lock = threading.Lock()
        self._ff_wall0 = None
        self._ff_sim0 = None

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
        time_tuple = tuple(int(t) for t in time_tuple)
        time_tuple += (0, tz.tzutc())
        d_utc = dt.datetime(*time_tuple)
        # then return it in local timezone
        return d_utc.astimezone(tz.tzutc())

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
        return dt.datetime.now(tz.tzlocal())

    def _fast_forward_enabled(self):
        return self["time_speedup"] != 1.0 or bool(self["time_start"])

    def ut(self):
        if not self._fast_forward_enabled():
            return dt.datetime.now(tz.tzutc())
        # scaled simulation clock (see __config__): anchor on the first call.
        # Double-checked locking: anchors are write-once, so once _ff_wall0
        # is visible the lock-free fast path below is safe.
        wall_now = dt.datetime.now(tz.tzutc())
        if self._ff_wall0 is None:
            with self._ff_lock:
                if self._ff_wall0 is None:
                    start = str(self["time_start"]).strip()
                    if start:
                        sim0 = dt.datetime.fromisoformat(start)
                        if sim0.tzinfo is None:
                            sim0 = sim0.replace(tzinfo=tz.tzutc())
                        self._ff_sim0 = sim0.astimezone(tz.tzutc())
                    else:
                        self._ff_sim0 = wall_now
                    # set last: readers test _ff_wall0, so _ff_sim0 must
                    # already be in place when they see it non-None
                    self._ff_wall0 = wall_now
        elapsed = (wall_now - self._ff_wall0).total_seconds() * self["time_speedup"]
        return self._ff_sim0 + dt.timedelta(seconds=elapsed)

    def utc_offset(self):
        offset = self.localtime().utcoffset()
        return (offset.days * 86400 + offset.seconds) / 3600.0

    def lst_in_rads(self, date=None):
        if not date:
            date = self.ut()
        return float(self._get_ephem(date=date).sidereal_time())

    def latitude_in_degs(self):
        return float(self["latitude"].to_d())

    def lst(self, date=None):
        """
        Mean Local Sidereal Time
        """
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

    # NOTE(thread-safety): the rise/set/twilight family below passes the
    # shared _sun/_moon bodies into next_rising/next_setting, which mutate
    # them — concurrent callers race on the shared body.
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
        # NOTE(thread-safety): compute-then-read on the shared _sun body is
        # not atomic; a concurrent sun method can recompute it in between.
        date = date or self.ut()
        self._sun.compute(self._get_ephem(date))

        return Position.from_alt_az(
            Coord.from_r(self._sun.alt), Coord.from_r(self._sun.az)
        )

    def sun_altitude(self, date=None):
        """
        Sun altitude in DEGREES.

        Prefer this over reading sunpos(): a float crosses the bus, a
        Position does not (it is not serializable), and unpacking sunpos()
        hands out Coords in radians that read like degrees.

        @rtype: float
        """
        date = date or self.ut()
        self._sun.compute(self._get_ephem(date))
        return float(Coord.from_r(self._sun.alt).to_d())

    def sun_azimuth(self, date=None):
        """
        Sun azimuth in DEGREES.

        The companion to sun_altitude(), and for the same reason: reading
        sunpos().az drags a Position across the bus, which is not
        serializable. Anything pointing away from the Sun needs this -
        twilight sky flats shoot the anti-solar point, 180 degrees from it.

        @rtype: float
        """
        date = date or self.ut()
        self._sun.compute(self._get_ephem(date))
        return float(Coord.from_r(self._sun.az).to_d())

    def is_dusk(self, date=None):
        """
        True while the Sun is on its way down, False while it is climbing.

        Which side of the day it is decides what a twilight routine should
        do when it runs out of sky: sky flats wait for a fainter sky at
        dusk and give up at dawn, and the other way around when the sky is
        too bright. The local clock cannot answer that question - it is the
        wall clock, so it says nothing about a simulated night run under
        `time_speedup`.

        The Sun is descending exactly when its last meridian crossing was a
        transit (its highest point) rather than an anti-transit.

        @rtype: bool
        """
        date = date or self.ut()
        site = self._get_ephem(date)
        return site.previous_transit(self._sun) > site.previous_antitransit(self._sun)

    def moonrise(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_rising(self._moon))

    def moonset(self, date=None):
        date = date or self.ut()
        site = self._get_ephem(date)
        return self._date_to_local(site.next_setting(self._moon))

    def moonpos(self, date=None):
        # NOTE(thread-safety): compute-then-read race on the shared _moon
        # body, same as sunpos.
        date = date or self.ut()
        self._moon.compute(self._get_ephem(date))

        return Position.from_alt_az(
            Coord.from_r(self._moon.alt), Coord.from_r(self._moon.az)
        )

    def moon_ra_dec(self, date=None):
        """
        Moon apparent TOPOCENTRIC position as (ra in HOURS, dec in DEGREES).

        The companion to sun_altitude()/sun_azimuth(): moonpos() returns a
        Position, which does not cross the bus. Computed against the
        observer, so the ~1 degree of horizontal parallax is included.

        @rtype: tuple(float, float)
        """
        date = date or self.ut()
        self._moon.compute(self._get_ephem(date))
        return (
            float(Coord.from_r(self._moon.ra).to_h()),
            float(Coord.from_r(self._moon.dec).to_d()),
        )

    def moonphase(self, date=None):
        # NOTE(thread-safety): compute-then-read race on the shared _moon
        # body, same as sunpos.
        date = date or self.ut()
        self._moon.compute(self._get_ephem(date))
        return self._moon.phase / 100.0

    def ra_to_ha(self, ra: float):
        # ra in hours
        # returns ha in hours, +/-12: east of the meridian is negative
        return float(
            CoordUtil.ra_to_ha(
                Coord.from_h(ra), Coord.from_r(self.lst_in_rads())
            ).to_h()
        )

    def ha_to_ra(self, ha: float):
        return float(
            CoordUtil.ha_to_ra(
                Coord.from_h(ha), Coord.from_r(self.lst_in_rads())
            ).to_h()
        )

    def ra_dec_to_alt_az(self, ra: float, dec: float, lst_in_rads: float | None = None):
        # ra in hours, dec in degrees, lst in radians
        # returns alt, az in degrees
        if not lst_in_rads:
            lst_in_rads = self.lst_in_rads()
        return Position.ra_dec_to_alt_az(ra, dec, self["latitude"].to_d(), lst_in_rads)

    def alt_az_to_ra_dec(
        self, alt: float, az: float, lst_in_rads: float | None = None
    ) -> tuple[float, float]:
        # alt, az in degrees, lst in radians
        # returns ra in hours, dec in degrees
        if not lst_in_rads:
            lst_in_rads = self.lst_in_rads()
        return Position.alt_az_to_ra_dec(alt, az, self["latitude"].to_d(), lst_in_rads)

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
