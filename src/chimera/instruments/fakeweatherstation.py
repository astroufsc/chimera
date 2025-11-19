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
    WeatherSeeing,
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
    WeatherSeeing,
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

    def seeing(self) -> float:
        """
        Returns a simulated seeing value in arcseconds that varies with time.
        Typical seeing ranges from 0.5 to 3.0 arcseconds.
        """
        # Seeing varies with hour, worse during day, better at night
        hour_radians = self._hour_in_radians()
        # Base seeing of 1.0 arcsec, varies ±0.5 with time, plus some random variation
        base_seeing = 1.0 + 0.5 * math.sin(hour_radians)
        noise = np.random.normal(0, 0.2)  # Add some random variation
        seeing_value = max(0.5, base_seeing + noise)  # Ensure minimum of 0.5
        return seeing_value

    def seeing_at_zenith(self) -> float:
        """
        Returns seeing corrected for zenith position.
        Typically better (smaller) than actual seeing.
        """
        current_seeing = self.seeing()
        # Zenith seeing is typically the seeing value corrected by airmass
        # For simplification, assume 20% better seeing at zenith
        return current_seeing * 0.8

    def flux(self) -> float:
        """
        Returns flux from the seeing monitor star in counts.
        Typical values range from 1000 to 50000 counts.
        """
        # Flux varies with atmospheric conditions and time
        hour_radians = self._hour_in_radians()
        base_flux = 10000 + 5000 * math.cos(hour_radians)
        noise = np.random.normal(0, 500)
        flux_value = max(100, base_flux + noise)
        return flux_value

    def airmass(self) -> float:
        """
        Returns the airmass of the seeing monitor star.
        Typical values range from 1.0 (zenith) to 3.0 (near horizon).
        """
        # Simulate airmass varying throughout the day
        hour_radians = self._hour_in_radians()
        # Airmass between 1.0 and 2.5
        airmass_value = 1.0 + 0.75 * (1 + math.sin(hour_radians))
        return airmass_value


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

    # Test seeing measurements
    seeing = fws.seeing()
    print(f"Seeing: {seeing:.2f} {fws.units['seeing']} @ {last_measurement_time}.")

    seeing_zenith = fws.seeing_at_zenith()
    print(
        f"Seeing at Zenith: {seeing_zenith:.2f} {fws.units['seeing_at_zenith']} @ {last_measurement_time}."
    )

    flux = fws.flux()
    print(f"Flux: {flux:.2f} {fws.units['flux']} @ {last_measurement_time}.")

    airmass = fws.airmass()
    print(f"Airmass: {airmass:.2f} {fws.units['airmass']} @ {last_measurement_time}.")

    print(f"Metadata: {fws.get_metadata(None)}")
