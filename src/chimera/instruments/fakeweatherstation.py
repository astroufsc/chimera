# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import math
from chimera.instruments.weatherstation import WeatherBase
from chimera.core.exceptions import OptionConversionException
from chimera.interfaces.weatherstation import WSValue, WeatherTemperature, WeatherHumidity, WeatherPressure, \
    WeatherWind, WeatherRain, WeatherTransparency
from astropy import units
from astropy.units import cds
import numpy as np
import datetime


class FakeWeatherStation(WeatherBase, WeatherTemperature, WeatherHumidity, WeatherPressure, WeatherWind, WeatherRain,
                         WeatherTransparency):
    def __init__(self):
        WeatherBase.__init__(self)

    def _hourinradians(self, hour):
        """
        For testing purposes, the function converts a given hour in radians.
        """
        return (math.pi / 12.) * hour

    def humidity(self, unit_out=units.pct):
        """
        Returns the 100% relative humidity in the range between 20% and 100%.
        :param unit: Unit in which the instrument should return the humidity.
        :return: the humidity.
        """
        current_time = datetime.datetime.utcnow()

        if unit_out not in self.__accepted_humidity_units__:
            raise OptionConversionException("Invalid humidity unit %s." % unit_out)

        humidity = 40 * math.cos(self._hourinradians(current_time.hour)) + 60.

        humidity = self._convert_units(
            humidity,
            units.pct,
            unit_out)

        return WSValue(current_time, humidity, unit_out)

    def temperature(self, unit_out=units.Celsius):
        """
        Returns the temperature in the chosen unit in the range between -10 C and +40 C.
        :param unit:  Unit in which the instrument should return the temperature.
        :return: the temperature.
        """

        current_time = datetime.datetime.utcnow()

        if unit_out not in self.__accepted_temperature_units__:
            raise OptionConversionException("Invalid temperature unit %s." % unit_out)

        temperature = 25 * math.sin(self._hourinradians(current_time.hour) - math.pi / 2.) + 15.

        temperature = self._convert_units(
            temperature,
            units.Celsius,
            unit_out,
            equivalencies=units.equivalencies.temperature())

        return WSValue(current_time, temperature, unit_out)

    def wind_speed(self, unit_out=units.meter / units.second):
        """
        Returns the wind speed in the chosen unit (Default: Meters per second).
        :param unit:  Unit in which the instrument should return the wind speed.
        :return: the wind speed.
        """

        reference_speed = 10  # M_PER_S

        if unit_out not in self.__accepted_speed_units__:
            raise OptionConversionException("Invalid speed unit %s." % unit_out)

        speed = self._convert_units(
            reference_speed,
            units.meter / units.second,
            unit_out)

        return WSValue(datetime.datetime.utcnow(), speed, unit_out)

    def wind_direction(self, unit_out=units.degree):
        """
        Returns the wind direction in the chosen unit in the range between 0 to 360 degrees.
        :param unit:  Unit in which the instrument should return the angle.
        :return: the angle.
        """
        if unit_out not in self.__accepted_direction_unit__:
            raise OptionConversionException("Invalid direction unit %s." % unit_out)

        hour = datetime.datetime.utcnow().hour

        reference_direction = 180 * math.sin(self._hourinradians(hour)) + 180

        direction = self._convert_units(
            reference_direction,
            units.degree,
            unit_out)

        return WSValue(datetime.datetime.utcnow(), direction, unit_out)

    def dew_point(self, unit_out=units.Celsius):
        """
        Some simulations ran on 'http://www.cactus2000.de/uk/unit/masshum.shtml' suggests that
        the dew point at 1.5mm Hg and low temperatures are very low, around -20 C.
        Here I'm using -10 C.

        :param unit:  Unit in which the instrument should return the temperature.
        :return: the angle.
        """

        if unit_out not in self.__accepted_temperature_units__:
            raise OptionConversionException("Invalid temperature unit %s." % unit_out)

        temperature = self._convert_units(
            10,
            units.Celsius,
            unit_out,
            equivalencies=units.equivalencies.temperature())

        return WSValue(datetime.datetime.utcnow(), temperature, unit_out)

    def pressure(self, unit_out=units.Pa):
        """
        Pressure at 1.5 atm
        :param unit:
        :return:
        """

        pressure_reference = 1140.  # MM_HG

        if unit_out not in self.__accepted_pressures_unit__:
            raise OptionConversionException("Invalid pressure unit %s." % unit_out)

        pressure = self._convert_units(pressure_reference, units.cds.mmHg, unit_out)

        return WSValue(datetime.datetime.utcnow(), pressure, unit_out)

    def rain_rate(self, unit_out=units.imperial.inch / units.hour):
        """
        For testing purposes, it never rains.
        :param unit:
        :return:
        """

        if unit_out not in self.__accepted_precipitation_unit__:
            raise OptionConversionException("Invalid precipitation unit %s." % unit_out)

        return WSValue(datetime.datetime.utcnow(), 0, unit_out)

    def isRaining(self):
        """
        Returns True for rain 20% of the time
        """
        return np.random.rand < 0.2

    def sky_transparency(self, unit_out=units.pct):
        """
        Returns, in percent, the sky transparency
        :param unit_out:
        """
        if unit_out not in self.__accepted_transparency_unit__:
            raise OptionConversionException("Invalid transparency unit %s." % unit_out)

        return WSValue(datetime.datetime.utcnow(), np.random.rand() * 100, unit_out)


if __name__ == '__main__':
    fws = FakeWeatherStation()

    humidity = fws.humidity(units.pct)
    print(('Humidity: %.2f %% @ %s.' % (humidity.value, humidity.time)))

    temperature = fws.temperature(units.imperial.deg_F)
    print(('Temperature: %.2f %s @ %s.' % (temperature.value, temperature.unit, temperature.time)))

    wind_speed = fws.wind_speed(units.kilometer / units.hour)
    print(('Wind Speed: %.2f %s @ %s.' % (wind_speed.value, wind_speed.unit, wind_speed.time)))

    wind_direction = fws.wind_direction(units.radian)
    print(('Wind Direction: %.2f %s @ %s.' % (wind_direction.value, wind_direction.unit, wind_direction.time)))

    dew_point = fws.dew_point(units.K)
    print(('Dew Point: %.2f %s @ %s.' % (dew_point.value, dew_point.unit, dew_point.time)))

    pressure = fws.pressure(units.cds.atm)
    print(('Pressure: %.2f %s @ %s.' % (pressure.value, pressure.unit, pressure.time)))

    rain = fws.rain_rate(unit_out=units.millimeter / units.hour)
    print(('Rain: %.2f %s @ %s.' % (rain.value, rain.unit, rain.time)))

    print(('Metadata: %s' % (fws.getMetadata(None))))
