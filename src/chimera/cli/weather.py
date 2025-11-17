#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime
import sys

from astropy.time import Time

from chimera.core.version import chimera_version
from chimera.util.output import green, red

from .cli import ChimeraCLI, action


class ChimeraWeather(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-weather", "Weather station script", chimera_version
        )

        self.add_help_group("ws", "Weather Station")
        self.add_help_group("commands", "Commands")

        self.add_instrument(
            name="weatherstation",
            cls="WeatherStation",
            required=True,
            help_group="ws",
            help="Weather Station instrument to be used",
        )

        self.add_parameters(
            dict(
                name="max_mins",
                short="t",
                type="float",
                default=10,
                help_group="commands",
                help="Mark in red date/time values if older than this time in minutes",
            )
        )

    @action(
        short="i",
        help="Print weather station current information",
        help_group="commands",
    )
    def info(self, options):
        self.out("=" * 80)
        self.out(
            "Weather Station: %s %s (%s)"
            % (
                self.weatherstation.get_location(),
                self.weatherstation["model"],
                self.weatherstation["device"],
            )
        )

        if self.weatherstation.features("WeatherSafety"):
            self.out(
                "Dome is %s to open" % green("SAFE")
                if self.weatherstation.is_safe_to_open()
                else red("NOT SAFE")
            )

        self.out("=" * 80)

        t = self.weatherstation.get_last_measurement_time()
        t = Time(t, format="fits")
        if datetime.datetime.now(datetime.UTC) - t.to_datetime(
            timezone=datetime.UTC
        ) > datetime.timedelta(minutes=options.max_mins):
            last_meas = red(t.iso)
        else:
            last_meas = green(t.iso)

        for attr in (
            "temperature",
            "dew_point",
            "humidity",
            "wind_speed",
            "wind_direction",
            "pressure",
            "rain_rate",
            "sky_transparency",
        ):
            v = getattr(self.weatherstation, attr)()
            self.out(
                f"{attr.replace('_', ' ').removeprefix('sky ')}:\t{v:.2f}\t{self.weatherstation.get_units(attr)}"
            )
        self.out(f"Last data:\t{last_meas}")
        self.out("=" * 80)


def main():
    cli = ChimeraWeather()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
