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

import astropy

from astropy import units
from astropy.units import cds


import datetime


class FakeWeatherStation(WeatherBase):
    def __init__(self):
        WeatherBase.__init__(self)

    def _hourinradians(self, hour):
        return (math.pi/12.) * hour

    def humidity(self, unit_out=units.pct):
        """
        Returns the 100% relative humidity in the range between 20% and 100%.
        :param unit: Unit in which the instrument should return the humidity.
        :return: the humidity.
        """
        hour = datetime.datetime.now().hour

        if unit_out not in self._accepted_humidity_units_:
            raise OptionConversionException("Invalid humidity unit %s." % unit_out)

        humidity = 40 * math.cos(self._hourinradians(hour)) + 60.

        humidity = self._convert_units(
            humidity,
            units.pct,
            unit_out)

        return humidity

    def temperature(self, unit_out=units.Celsius):
        """
        Returns the temperature in the chosen unit in the range between -10 C and +40 C.
        :param unit:  Unit in which the instrument should return the temperature.
        :return: the temperature.
        """

        hour = datetime.datetime.now().hour

        _accepted_temperature_unit = [
            units.Celsius,
            units.Kelvin,
            units.imperial.deg_F
        ]

        if unit_out not in _accepted_temperature_unit:
            raise OptionConversionException("Invalid temperature unit %s." % unit_out)

        temperature = 25 * math.sin(self._hourinradians(hour) - math.pi/2.) + 15.

        temperature = self.convert_units(
          temperature,
          units.Celsius,
          unit_out,
          equivalencies=units.equivalencies.temperature())

        return temperature

    def wind_speed(self, unit_out=units.meter/units.second):
        """
        Returns the wind speed in the chosen unit (Default: Meters per second).
        :param unit:  Unit in which the instrument should return the wind speed.
        :return: the wind speed.
        """

        reference_speed = 10  # M_PER_S

        _accepted_speed_unit = [
            units.meter / units.second,
            units.kilometer / units.hour,
            units.imperial.mile / units.hour,
            units.imperial.foot / units.second,
        ]

        if unit_out not in _accepted_speed_unit:
            raise OptionConversionException("Invalid speed unit %s." % unit_out)

        speed = self.convert_units(
            reference_speed,
            units.meter / units.second,
            unit_out)

        return speed

    def wind_direction(self, unit_out=units.degree):
        """
        Returns the wind direction in the chosen unit in the range between 0 to 360 degrees.
        :param unit:  Unit in which the instrument should return the angle.
        :return: the angle.
        """
        _accepted_direction_unit = [
            units.degree,
            units.radian
        ]

        if unit_out not in _accepted_direction_unit:
            raise OptionConversionException("Invalid direction unit %s." % unit_out)

        hour = datetime.datetime.now().hour

        reference_direction = 180 * math.sin(self._hourinradians(hour)) + 180

        direction = self.convert_units(
            reference_direction,
            units.degree,
            unit_out)

        return direction

    def dew_point(self, unit_out=units.Celsius):
        """
        Some simulations ran on 'http://www.cactus2000.de/uk/unit/masshum.shtml' suggests that
        the dew point at 1.5mm Hg and low temperatures are very low, around -20 C.
        Here I'm using -10 C.

        :param unit:  Unit in which the instrument should return the temperature.
        :return: the angle.
        """

        _accepted_temperature_unit = [
            units.Celsius,
            units.Kelvin,
            units.imperial.deg_F
        ]

        if unit_out not in _accepted_temperature_unit:
            raise OptionConversionException("Invalid temperature unit %s." % unit_out)

        temperature = self.convert_units(
          10,
          units.Celsius,
          unit_out,
          equivalencies=units.equivalencies.temperature())

        return temperature

    def pressure(self, unit_out=units.cds.mmHg):
        """
        Pressure at 1.5 atm
        :param unit:
        :return:
        """
        pressure_reference = 1140.  # MM_HG

        _accepted_pressures_unit = [
            units.cds.mmHg,
            units.bar,
            units.cds.atm,
            units.Pa]
            # units.imperial.psi  - my astropy version does not have psi

        if unit_out not in _accepted_pressures_unit :
            raise OptionConversionException("Invalid pressure unit %s." % unit_out)

        pressure = self.convert_units(
            pressure_reference,
            units.cds.mmHg,
            unit_out)

        return pressure

    def rain(self, unit_out=units.liter / units.hour):
        """
        For testing purposes, it never rains.
        :param unit:
        :return:
        """

        return 0.


if __name__ == '__main__':

    fws = FakeWeatherStation()

    print('Humidity: %.2f %%.' % fws.humidity(units.pct))
    # print('Temperature: %.2f %s.' % (fws.temperature(units.imperial.deg_F), units.imperial.deg_F))

    # print('Wind Speed: %.2f %s.' % (fws.wind_speed(units.kilometer / units.hour), (units.kilometer/units.hour)))
    # print('Wind Direction: %.2f %s.' % (fws.wind_direction(units.radian), units.radian))

    # print('Dew Point: %.2f %s.' % (fws.dew_point(units.K), units.K))

    # print('Pressure: %.2f %s.' % (fws.pressure(units.cds.atm), units.cds.atm))
    # print('Rain: %.2f mm/h.' % fws.rain())


