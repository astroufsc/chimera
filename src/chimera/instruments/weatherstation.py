# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.weatherstation import WeatherStation


class WeatherBase(ChimeraObject, WeatherStation):
    def __init__(self):
        ChimeraObject.__init__(self)

    def get_metadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        md = [("ENVMOD", str(self["model"]), "Weather station Model")]

        # Last Measurement Time
        md += [
            (
                "ENVDATE",
                self.get_last_measurement_time(),
                "Weather station measurement date/time",
            )
        ]

        # Temperature
        if self.features("WeatherTemperature"):
            temp, dew = self.temperature(), self.dew_point()
            md += [
                (
                    "ENVTEM",
                    round(temp, 2),
                    (f"[{self.units['temperature']}] Weather station temperature"),
                ),
                (
                    "ENVDEW",
                    round(dew, 2),
                    (f"[{self.units['dew_point']}] Weather station dew point"),
                ),
            ]

        # Humidity
        if self.features("WeatherHumidity"):
            hum = self.humidity()
            md += [
                (
                    "ENVHUM",
                    round(hum, 2),
                    (f"[{self.units['humidity']}] Weather station relative humidity"),
                )
            ]
        # Wind
        if self.features("WeatherWind"):
            speed, direc = self.wind_speed(), self.wind_direction()
            md += [
                (
                    "ENVWIN",
                    round(speed, 2),
                    (f"[{self.units['wind_speed']}] Weather station wind speed"),
                ),
                (
                    "ENVDIR",
                    round(direc, 2),
                    (
                        f"[{self.units['wind_direction']}] Weather station wind direction"
                    ),
                ),
            ]

        # Pressure
        if self.features("WeatherPressure"):
            press = self.pressure()
            md += [
                (
                    "ENVPRE",
                    round(press, 2),
                    (f"[{self.units['pressure']}] Weather station air pressure"),
                )
            ]

        # Sky Transparency
        if self.features("WeatherTransparency"):
            transp = self.sky_transparency()
            md += [
                (
                    "ENVSKT",
                    round(transp, 2),
                    (
                        f"[{self.units['sky_transparency']}] Weather station Sky Transparency"
                    ),
                )
            ]

        # Safe to open
        if self.features("WeatherSafety"):
            safe = self.is_safe_to_open()
            md += [("ENVSAFE", safe, "Weather station safe to open flag")]

        return md
