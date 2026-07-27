# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime as dt
import time

import msgspec
import pytest
from dateutil.relativedelta import relativedelta

from chimera.core.site import Site

SITE_CONFIG = {
    "name": "UFSC",
    "latitude": "-27 36 13 ",
    "longitude": "-48 31 20",
    "altitude": "20",
}


class TestSite:
    def test_times(self, manager):
        manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13 ",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

        site = manager.get_proxy("/Site/0")

        print()
        print("UT   :", site.ut())
        print("JD   :", site.jd())
        print("MJD  :", site.mjd())

    @pytest.mark.skip
    def test_sidereal_clock(self, manager):
        manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13 ",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

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
        manager.add_class(
            Site,
            "lna",
            {
                "name": "UFSC",
                "latitude": "-27 36 13 ",
                "longitude": "-48 31 20",
                "altitude": "20",
            },
        )

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
        manager.add_class(Site, "lna", SITE_CONFIG)
        site = manager.get_proxy("/Site/0")

        when = dt.datetime(2026, 7, 27, 16, 0, tzinfo=dt.UTC)

        assert site.sun_altitude(when) == pytest.approx(float(site.sunpos(when).alt))
        assert site.sun_altitude() == pytest.approx(float(site.sunpos().alt), abs=0.01)

    def test_sun_altitude_survives_the_bus(self, manager):
        """A Position cannot be encoded, so sunpos() only works between
        objects sharing a bus - the reason for a plain-float accessor."""
        manager.add_class(Site, "lna", SITE_CONFIG)
        site = manager.get_proxy("/Site/0")

        encoder = msgspec.json.Encoder()
        assert encoder.encode(site.sun_altitude())

        with pytest.raises(TypeError):
            encoder.encode(site.sunpos())

    def test_is_dusk_tracks_the_sun_not_the_clock(self, manager):
        """Dusk is the sun on its way down, sampled all the way around a
        day and checked against the altitude it is about to have."""
        manager.add_class(Site, "lna", SITE_CONFIG)
        site = manager.get_proxy("/Site/0")

        midnight = dt.datetime(2026, 7, 27, 0, 0, tzinfo=dt.UTC)
        for hour in range(24):
            when = midnight + dt.timedelta(hours=hour)
            descending = site.sun_altitude(
                when + dt.timedelta(minutes=1)
            ) < site.sun_altitude(when)
            assert site.is_dusk(when) is descending, f"{when} is not settled"
