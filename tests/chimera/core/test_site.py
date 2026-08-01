# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime as dt
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

    def test_the_night_boundary_defaults_to_astronomical_twilight(self, manager):
        """-18 deg was hardcoded before it was configurable; the default has
        to reproduce it exactly or every existing schedule shifts."""
        site = manager.get_proxy("/Site/0")

        when = dt.datetime(2026, 7, 27, 12, 0, tzinfo=dt.UTC)

        assert site["horizon"]["night"] == -18.0

        # next_setting() places the sun's UPPER LIMB on the horizon while
        # sun_altitude() reports its centre, so the altitude at the returned
        # instant sits one solar semi-diameter (~0.27 deg) lower
        assert site.sun_altitude(site.sunset_twilight_end(when)) == pytest.approx(
            -18.0, abs=0.3
        )
        assert site.sun_altitude(site.sunrise_twilight_begin(when)) == pytest.approx(
            -18.0, abs=0.3
        )
        # the bracket is derived, not pinned: -18 + 6 = the historical -12
        assert site.sun_altitude(site.sunset_twilight_begin(when)) == pytest.approx(
            -12.0, abs=0.3
        )

    def test_raising_the_night_horizon_lengthens_the_night(self, manager):
        """Raising the boundary EXTENDS the observing window at both ends:
        descending, the sun reaches -8 before -18, so the night starts
        earlier; rising, it reaches -8 after -18, so it ends later. That is
        the point - a site whose twilight calibrations cannot begin until
        -8 should keep observing until then instead of handing the sky over
        at -18 and waiting (lna40 PENDING_ISSUES 50)."""
        from chimera.core.site import Site

        site = manager.get_proxy("/Site/0")
        when = dt.datetime(2026, 7, 27, 12, 0, tzinfo=dt.UTC)
        dusk18, dawn18 = (
            site.sunset_twilight_end(when),
            site.sunrise_twilight_begin(when),
        )

        manager.add_class(Site, "longnight", {"horizon": {"night": -8.0}}, True)
        try:
            short = manager.get_proxy("/Site/longnight")

            assert short.sun_altitude(short.sunset_twilight_end(when)) == pytest.approx(
                -8.0, abs=0.3
            )
            # the derived bracket followed it and stayed above: -8 + 6 = -2
            assert short.sun_altitude(
                short.sunset_twilight_begin(when)
            ) == pytest.approx(-2.0, abs=0.3)
            # starts earlier at dusk, ends later at dawn: strictly more sky
            assert short.sunset_twilight_end(when) < dusk18
            assert short.sunrise_twilight_begin(when) > dawn18
        finally:
            manager.remove("/Site/longnight")

    def test_an_inverted_horizon_pair_is_refused_at_startup(self, manager):
        """a twilight bracket below the night boundary turns every window inside
        out; fail at start rather than at the first dusk."""
        from chimera.core.site import Site

        with pytest.raises(Exception):
            manager.add_class(
                Site,
                "inverted",
                {"horizon": {"night": -6.0, "twilight": -12.0}},
                True,
            )

    def test_an_unknown_horizon_key_is_refused(self, manager):
        """A dict option cannot be spell-checked by the config layer, so a
        typo would silently fall back to the defaults."""
        from chimera.core.site import Site

        with pytest.raises(Exception):
            manager.add_class(Site, "typo", {"horizon": {"nite": -8.0}}, True)
