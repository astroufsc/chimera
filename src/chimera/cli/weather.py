#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime
import sys

from chimera.core.version import _chimera_version_
from chimera.interfaces.weatherstation import WeatherSafety
from chimera.util.output import green, red

from .cli import ChimeraCLI, action


class ChimeraWeather(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-weather", "Weather station script", _chimera_version_
        )

        self.addHelpGroup("WS", "Weather Station")
        self.addHelpGroup("COMMANDS", "Commands")

        self.addInstrument(
            name="weatherstation",
            cls="WeatherStation",
            required=True,
            helpGroup="WS",
            help="Weather Station instrument to be used",
        )

        self.addParameters(
            dict(
                name="max_mins",
                short="t",
                type="float",
                default=10,
                helpGroup="COMMANDS",
                help="Mark in red date/time values if older than this time in minutes",
            )
        )

    @action(
        short="i",
        help="Print weather station current information",
        helpGroup="COMMANDS",
    )
    def info(self, options):
        self.out("=" * 80)
        self.out(
            "Weather Station: %s %s (%s)"
            % (
                self.weatherstation.getLocation(),
                self.weatherstation["model"],
                self.weatherstation["device"],
            )
        )

        if self.weatherstation.features(WeatherSafety):
            self.out(
                "Dome is %s to open" % green("OK")
                if self.weatherstation.okToOpen()
                else red("NOT OK")
            )

        self.out("=" * 80)

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
            try:
                v = self.weatherstation.__getattr__(attr)()
                if isinstance(v, NotImplementedError) or not v:
                    continue
                t = (
                    red(v.time.__str__())
                    if datetime.datetime.utcnow() - v.time
                    > datetime.timedelta(minutes=self.options.max_mins)
                    else green(v.time.__str__())
                )
                self.out(
                    t
                    + "  "
                    + attr.replace("_", " ")
                    + ": {0.value:.2f} {0.unit:s} ".format(v)
                )
            except NotImplementedError:
                pass
            except AttributeError:
                pass

        self.out("=" * 80)

        return


def main():
    cli = ChimeraWeather()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
