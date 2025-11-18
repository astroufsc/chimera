# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
from chimera.core.interface import Interface


class WeatherStation(Interface):
    """
    Instrument interface for weather stations.

    __config__ keys:
        device (str or None): Identifier or path for the weather station device (e.g., serial port, network address, or device name). Should be set to the appropriate value for the specific hardware.
        model (str): The model name or identifier of the weather station. Defaults to "unknown" if not specified.
    """

    __config__ = {
        "device": None,  # weather station device (str or None)
        "model": "unknown",  # weather station model (str)
    }

    # Helping dictionary for units used in weather station interfaces. They should be convertable using astropy.units.Unit()
    units = {
        "temperature": "deg_C",
        "dew_point": "deg_C",
        "humidity": "%",
        "pressure": "Pa",
        "wind_speed": "m/s",
        "wind_direction": "deg",
        "rain_rate": "mm/h",
        "sky_transparency": "%",
    }

    def get_units(self, u: str | None) -> str | dict:
        """
        Returns a dictionary with the units used by the weather station.
        The keys are: temperature, dew_point, humidity, pressure, wind_speed, wind_direction, rain_rate, sky_transparency
        The values are strings representing the units, compatible with astropy.units.Unit()
        @param u: The key for which to retrieve the unit. If None, return all units.
        @return: A string representing the unit if u is provided, otherwise a dictionary with all units.
        """
        if u is not None:
            if u in self.units:
                return self.units[u]
            else:
                # Raise a KeyError if the unit key is unknown
                raise KeyError(f"Unknown unit key: {u}")
        return self.units

    def get_last_measurement_time(self) -> str:
        """
        Returns the timestamp of the last measurement taken by the weather station.

        @return: The UTC time of the last measurement as a string in FITS format ("YYYY-MM-DDThh:mm:ss.sss").
                 E.g.: '2025-11-17T21:46:41.896'
                 Can be converted into an astropy Time object using:
                 Time('2025-11-17T21:46:41.896', format="fits")
        """
        pass


class WeatherHumidity(WeatherStation):
    """
    Humidity units accepted by the interface.
    """

    def humidity(self) -> float:
        """
        Returns the 100% relative humidity in percentage.
        @return: the humidity.
        """


class WeatherTemperature(WeatherStation):
    """
    Methods related to temperature
    """

    def temperature(self) -> float:
        """
        Returns the temperature in Celsius.
        @return: the temperature.
        """

    def dew_point(self) -> float:
        """
        Returns the dew point temperature in Celsius.
        @return: the dew point temperature.
        """


class WeatherWind(WeatherStation):
    """
    Methods related to wind
    """

    def wind_speed(self) -> float:
        """
        Returns the wind speed in meters per second.
        @return: the wind speed.
        """

    def wind_direction(self) -> float:
        """
        Returns the wind direction in Degrees.
        @return: the wind direction.
        """


class WeatherPressure(WeatherStation):
    """
    Methods related to pressure
    """

    def pressure(self) -> float:
        """
        Returns the atmospheric pressure in Pascals.
        @return: the pressure.
        """


class WeatherRain(WeatherStation):
    """
    Methods related to rain
    """

    def rain_rate(self) -> float:
        """
        Returns the precipitation rate in mm/hour.
        @return: the precipitation rate.
        """

    def is_raining(self) -> bool:
        """
        Returns True if it is raining and False otherwise
        """


class WeatherTransparency(WeatherStation):
    """
    Methods related to cloud and sky transparency
    """

    def sky_transparency(self) -> float:
        """
        Returns sky transparency, or 100% - clouds coverage.

        For a system with only two/three stages, the suggestion is to use:
        0% for overcast, 50% to cloudy and 100% to clear
        """


class WeatherSafety(WeatherStation):
    """
    Methods related to weather environment safety.

    Some weather stations can have some intelligence that returns to the OCS only if it is okay to open the dome or not.
    """

    def ok_to_open(self) -> bool:
        """
        Returns True if it is okay to open the dome and False otherwise.
        """
