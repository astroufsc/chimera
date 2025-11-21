# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import time

import pytest
from dateutil.relativedelta import relativedelta

from chimera.core.site import Site


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

        try:
            print()
            print("local:", site.localtime())
            print("UT   :", site.ut())
            print("JD   :", site.JD())
            print("MJD  :", site.MJD())
            print("LST  :", site.LST())
            print("GST  :", site.GST())
        except Exception as e:
            print(e)

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

        site = manager.get_proxy(Site)

        try:
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

        except Exception as e:
            print(e)

    def test_site_name_configuration(self, manager):
        """Test that site name from configuration is properly set and appears in metadata"""
        # Add a site with a custom name
        manager.add_class(
            Site,
            "test_site",
            {
                "name": "Swope",
                "latitude": "-70:42:00.877",
                "longitude": "-29:00:43.175",
                "altitude": "2187",
            },
        )

        site = manager.get_proxy("/Site/0")

        # Verify the name was properly set
        assert site["name"] == "Swope", f"Site name should be 'Swope' but got '{site['name']}'"

        # Verify the metadata contains the correct name
        metadata = site.get_metadata(None)
        site_metadata = [item for item in metadata if item[0] == "SITE"]
        assert len(site_metadata) == 1, "Should have exactly one SITE entry in metadata"
        assert (
            site_metadata[0][1] == "Swope"
        ), f"SITE header should be 'Swope' but got '{site_metadata[0][1]}'"
