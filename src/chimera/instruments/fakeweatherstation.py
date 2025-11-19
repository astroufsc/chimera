# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime
import math

import numpy as np

from chimera.instruments.weatherstation import WeatherStationBase
from chimera.interfaces.weatherstation import (
    WeatherHumidity,
    WeatherPressure,
    WeatherRain,
    WeatherSafety,
    WeatherTemperature,
    WeatherTransparency,
    WeatherWind,
)


class FakeWeatherStation(
    WeatherStationBase,
    WeatherTemperature,
    WeatherHumidity,
    WeatherPressure,
    WeatherWind,
    WeatherRain,
    WeatherTransparency,
    WeatherSafety,
):
    def __init__(self):
        WeatherStationBase.__init__(self)
        self["model"] = "FakeWeatherStation v1.0"

    def _hour_in_radians(self, hour=datetime.datetime.now(datetime.UTC).hour):
        """
        For testing purposes, the function converts a given hour in radians.
        """
        return (math.pi / 12.0) * hour

    def get_last_measurement_time(self):
        return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")

    def humidity(self):
        humidity = 40 * math.cos(self._hour_in_radians()) + 60.0
        return humidity

    def temperature(self):
        temperature = 25 * math.sin(self._hour_in_radians() - math.pi / 2.0) + 15.0
        return temperature

    def wind_speed(self):
        reference_speed = 10  # M_PER_S
        return reference_speed

    def wind_direction(self):
        reference_direction = 180 * math.sin(self._hour_in_radians()) + 180
        return reference_direction

    def dew_point(self):
        """
        Some simulations ran on 'http://www.cactus2000.de/uk/unit/masshum.shtml' suggests that
        the dew point at 1.5mm Hg and low temperatures are very low, around -20 C.
        Here I'm using -10 C.
        """
        return -10.0

    def pressure(self):
        """
        Pressure at 1.5 atm
        """
        pressure_reference = 151987.5  # Pa
        return pressure_reference

    def rain_rate(self):
        return 0.0

    def is_raining(self):
        """
        Returns True for rain 20% of the time
        """
        return np.random.rand() < 0.2

    def sky_transparency(self):
        """
        Returns, in percent, the sky transparency
        """
        return 84.0

    def is_safe_to_open(self):
        """
        Fake weather station is always safe to open
        """
        return True


if __name__ == "__main__":
    fws = FakeWeatherStation()

    last_measurement_time = fws.get_last_measurement_time()

    humidity = fws.humidity()
    print(f"Humidity: {humidity:.2f} % @ {last_measurement_time}.")

    temperature = fws.temperature()
    print(
        f"Temperature: {temperature:.2f} {fws.units['temperature']} @ {last_measurement_time}."
    )

    wind_speed = fws.wind_speed()
    print(
        f"Wind Speed: {wind_speed:.2f} {fws.units['wind_speed']} @ {last_measurement_time}."
    )

    wind_direction = fws.wind_direction()
    print(
        f"Wind Direction: {wind_direction:.2f} {fws.units['wind_direction']} @ {last_measurement_time}."
    )

    dew_point = fws.dew_point()
    print(
        f"Dew Point: {dew_point:.2f} {fws.units['dew_point']} @ {last_measurement_time}."
    )

    pressure = fws.pressure()
    print(
        f"Pressure: {pressure:.2f} {fws.units['pressure']} @ {last_measurement_time}."
    )

    rain = fws.rain_rate()
    print(f"Rain: {rain:.2f} {fws.units['rain_rate']} @ {last_measurement_time}.")

    print(f"Metadata: {fws.get_metadata(None)}")
