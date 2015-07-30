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

from chimera.interfaces.weatherstation import Humidity, Temperature, Speed
from chimera.interfaces.weatherstation import Direction, Pressure, Rain

from astropy import units
from astropy.units import cds


import datetime
from collections import namedtuple


class FakeWeatherStation(WeatherBase):
    def __init__(self):
        WeatherBase.__init__(self)

    def _hourinradians(self, hour):
        """
        For testing purposes, the function converts a given hour in radians.
        """
        return (math.pi/12.) * hour

    def humidity(self, unit_out=units.pct):
        """
        Returns the 100% relative humidity in the range between 20% and 100%.
        :param unit: Unit in which the instrument should return the humidity.
        :return: the humidity.
        """
        current_time = datetime.datetime.now()

        if unit_out not in self.__accepted_humidity_units__:
            raise OptionConversionException("Invalid humidity unit %s." % unit_out)

        humidity = 40 * math.cos(self._hourinradians(current_time.hour)) + 60.

        humidity = self._convert_units(
            humidity,
            units.pct,
            unit_out)

        return Humidity(current_time, humidity)

    def temperature(self, unit_out=units.Celsius):
        """
        Returns the temperature in the chosen unit in the range between -10 C and +40 C.
        :param unit:  Unit in which the instrument should return the temperature.
        :return: the temperature.
        """

        current_time = datetime.datetime.now()

        if unit_out not in self.__accepted_temperature_units__:
            raise OptionConversionException("Invalid temperature unit %s." % unit_out)

        temperature = 25 * math.sin(self._hourinradians(current_time.hour) - math.pi/2.) + 15.

        temperature = self._convert_units(
            temperature,
            units.Celsius,
            unit_out,
            equivalencies=units.equivalencies.temperature())

        return Temperature(current_time, temperature)

    def wind_speed(self, unit_out=units.meter/units.second):
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

        return Speed(datetime.datetime.now(), speed)

    def wind_direction(self, unit_out=units.degree):
        """
        Returns the wind direction in the chosen unit in the range between 0 to 360 degrees.
        :param unit:  Unit in which the instrument should return the angle.
        :return: the angle.
        """
        if unit_out not in self.__accepted_direction_unit__:
            raise OptionConversionException("Invalid direction unit %s." % unit_out)

        hour = datetime.datetime.now().hour

        reference_direction = 180 * math.sin(self._hourinradians(hour)) + 180

        direction = self._convert_units(
            reference_direction,
            units.degree,
            unit_out)

        return Direction(datetime.datetime.now(), direction)

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

        return Temperature(datetime.datetime.now(), temperature)

    def pressure(self, unit_out=units.cds.mmHg):
        """
        Pressure at 1.5 atm
        :param unit:
        :return:
        """
        pressure_reference = 1140.  # MM_HG

        if unit_out not in self.__accepted_pressures_unit__:
            raise OptionConversionException("Invalid pressure unit %s." % unit_out)

        pressure = self._convert_units(
            pressure_reference,
            units.cds.mmHg,
            unit_out)

        return Pressure(datetime.datetime.now(), pressure)

    def rain(self, unit_out=units.liter / units.hour):
        """
        For testing purposes, it never rains.
        :param unit:
        :return:
        """

        return Rain(datetime.datetime.now(), 0)

if __name__ == '__main__':

    fws = FakeWeatherStation()

    humidity = fws.humidity(units.pct)
    print('Humidity: %.2f %% @ %s.' % (humidity.humidity, humidity.time))

    temperature = fws.temperature(units.imperial.deg_F)
    print('Temperature: %.2f %s @ %s.' % (temperature.temperature, units.imperial.deg_F, temperature.time))

    wind_speed = fws.wind_speed(units.kilometer / units.hour)
    print('Wind Speed: %.2f %s @ %s.' % (wind_speed.speed, (units.kilometer/units.hour), wind_speed.time))

    wind_direction = fws.wind_direction(units.radian)
    print('Wind Direction: %.2f %s @ %s.' % (wind_direction.direction, units.radian, wind_direction.time))

    dew_point = fws.dew_point(units.K)
    print('Dew Point: %.2f %s @ %s.' % (dew_point.temperature, units.K, dew_point.time))

    pressure = fws.pressure(units.cds.atm)
    print('Pressure: %.2f %s @ %s.' % (pressure.pressure, units.cds.atm, pressure.time))

    rain = fws.rain()
    print('Rain: %.2f @ %s.' % (rain.rain, rain.time))
