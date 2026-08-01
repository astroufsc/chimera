# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime as dt
import math
import time

import msgspec
import pytest
from dateutil.relativedelta import relativedelta


class TestSite:
    # the manager fixture injects a local Site; these tests keep using the
    # proxy on purpose: the site must stay reachable over the bus
    def test_times(self, manager):
        site = manager.get_proxy("/Site/0")

        print()
        print("UT   :", site.ut())
        print("JD   :", site.jd())
        print("MJD  :", site.mjd())

    @pytest.mark.skip
    def test_sidereal_clock(self, manager):
        site = manager.get_proxy("/Site/0")

        times = []
        real_times = []

        for i in range(100):
            t0 = time.clock()
            t0_r = time.time()
            print(f"\r{site.LST()}", end=" ")
            times.append(time.clock() - t0)
            real_times.append(time.time() - t0_r)

        print()
        print(sum(times) / len(times))
        print(sum(real_times) / len(real_times))

    def test_astros(self, manager):
        site = manager.get_proxy("/Site/0")

        print()
        print("local   :", site.localtime())
        print()
        print("moonrise  :", site.moonrise())
        print("moonset   :", site.moonset())
        print("moon pos  :", site.moonpos())
        print("moon phase:", site.moonphase())
        print()
        print("sunrise:", site.sunrise())
        print("sunset :", site.sunset())
        print("sun pos:", site.sunpos())
        print()

        sunset_twilight_begin = site.sunset_twilight_begin()
        sunset_twilight_end = site.sunset_twilight_end()
        sunset_twilight_duration = relativedelta(
            sunset_twilight_end, sunset_twilight_begin
        )

        sunrise_twilight_begin = site.sunrise_twilight_begin()
        sunrise_twilight_end = site.sunrise_twilight_end()
        sunrise_twilight_duration = relativedelta(
            sunrise_twilight_end, sunrise_twilight_begin
        )

        print("next sunset twilight begins at:", sunset_twilight_begin)
        print("next sunset twilight ends   at:", sunset_twilight_end)
        print("sunset twilight duration      :", sunset_twilight_duration)
        print()
        print("next sunrise twilight begins at:", sunrise_twilight_begin)
        print("next sunrise twilight ends   at:", sunrise_twilight_end)
        print("sunrise twilight duration      :", sunrise_twilight_duration)

    def test_sun_altitude_is_the_altitude_in_degrees(self, manager):
        site = manager.get_proxy("/Site/0")

        when = dt.datetime(2026, 7, 27, 16, 0, tzinfo=dt.UTC)

        assert site.sun_altitude(when) == pytest.approx(float(site.sunpos(when).alt))
        assert site.sun_altitude() == pytest.approx(float(site.sunpos().alt), abs=0.01)

    def test_sun_azimuth_is_the_azimuth_in_degrees(self, manager):
        site = manager.get_proxy("/Site/0")

        when = dt.datetime(2026, 7, 27, 16, 0, tzinfo=dt.UTC)

        assert site.sun_azimuth(when) == pytest.approx(float(site.sunpos(when).az))
        assert site.sun_azimuth() == pytest.approx(float(site.sunpos().az), abs=0.01)

    def test_sun_accessors_survive_the_bus(self, manager):
        """A Position cannot be encoded, so sunpos() only works between
        objects sharing a bus - the reason for the plain-float accessors."""
        site = manager.get_proxy("/Site/0")

        encoder = msgspec.json.Encoder()
        assert encoder.encode(site.sun_altitude())
        assert encoder.encode(site.sun_azimuth())

        with pytest.raises(TypeError):
            encoder.encode(site.sunpos())

    def test_ra_to_ha_is_signed_around_the_meridian(self, manager):
        """HA comes back in [-12, +12), east of the meridian negative, even
        for a right ascension on the other side of the 0/24 h wrap."""
        site = manager.get_proxy("/Site/0")
        lst = site.lst_in_rads() * 12 / math.pi

        for hour_angle in (-11.5, -1, 0, 1, 11.5):
            ra = (lst - hour_angle) % 24
            # the sidereal clock keeps running: 0.01 h is 36 seconds of slack
            assert site.ra_to_ha(ra) == pytest.approx(hour_angle, abs=0.01)

    def test_is_dusk_tracks_the_sun_not_the_clock(self, manager):
        """Dusk is the sun on its way down, sampled all the way around a
        day and checked against the altitude it is about to have."""
        site = manager.get_proxy("/Site/0")

        midnight = dt.datetime(2026, 7, 27, 0, 0, tzinfo=dt.UTC)
        for hour in range(24):
            when = midnight + dt.timedelta(hours=hour)
            descending = site.sun_altitude(
                when + dt.timedelta(minutes=1)
            ) < site.sun_altitude(when)
            assert site.is_dusk(when) is descending, f"{when} is not settled"

    def test_moon_ra_dec_survives_the_bus_and_includes_parallax(self, manager):
        """moonpos() cannot be encoded and a bare pyephem Moon is geocentric:
        this must cross the bus AND include the observer's parallax."""
        import ephem

        site = manager.get_proxy("/Site/0")
        when = dt.datetime(2026, 7, 31, 3, 0, tzinfo=dt.UTC)

        ra, dec = site.moon_ra_dec(when)

        encoder = msgspec.json.Encoder()
        assert encoder.encode(site.moon_ra_dec())
        with pytest.raises(TypeError):
            encoder.encode(site.moonpos())

        assert 0.0 <= ra < 24.0
        assert -90.0 <= dec <= 90.0

        # geocentric, for contrast
        geo = ephem.Moon()
        geo.compute(when.strftime("%Y/%m/%d %H:%M:%S"))
        geo_ra = math.degrees(float(geo.ra)) / 15.0
        geo_dec = math.degrees(float(geo.dec))

        sep = math.hypot(
            (ra - geo_ra) * 15.0 * math.cos(math.radians(dec)), dec - geo_dec
        )
        assert sep > 0.05, (
            f"moon_ra_dec() returned the geocentric position (sep {sep:.3f} deg); "
            "it must be computed against the observer"
        )
        assert sep < 1.5, f"parallax should be under ~1 deg, got {sep:.3f}"
