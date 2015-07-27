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
from chimera.interfaces.weatherstation import Unit

import datetime


class FakeWeatherStation(WeatherBase):
    def __init__(self):
        WeatherBase.__init__(self)


    def _celsius_to_kelvin(self, temperature):
        """
        Given a temperature in Celsius, returns it in Kelvin
        :param temperature: in Celsius
        :return: temperature em Kelvin
        """
        return temperature + 273.15

    def _celsius_to_fahrenheit(self, temperature):
        """
        Given a temperature in Celsius, returns it in Fahrenheit
        :param temperature: in Celsius
        :return: temperature em Fahrenheit
        """
        return (temperature * 9./5.) + 32.

    def _hourinradians(self, hour):
        return (math.pi/12.) * hour

    def humidity(self, unit=Unit.PERCENTUAL):
        """
        Returns the 100% relative humidity in the range between 20% and 100%.
        :param unit: Unit in which the instrument should return the humidity.
        :return: the humidity.
        """
        hour = datetime.datetime.now().hour

        return 40 * math.cos(self._hourinradians(hour)) + 60.

    def temperature(self, unit=Unit.CELSIUS):
        """
        Returns the temperature in the chosen unit in the range between -10 C and +40 C.
        :param unit:  Unit in which the instrument should return the temperature.
        :return: the temperature.
        """

        hour = datetime.datetime.now().hour

        temperature = 25 * math.sin(self._hourinradians(hour) - math.pi/2.) + 15.

        if unit == Unit.FAHRENHEIT:
            temperature = self._celsius_to_fahrenheit(temperature)
        elif unit == Unit.KELVIN:
            temperature = self._celsius_to_kelvin(temperature)

        return temperature

    def wind_speed(self, unit=Unit.M_PER_S):
        """
        Returns the wind speed in the chosen unit (Default: Meters per second).
        :param unit:  Unit in which the instrument should return the wind speed.
        :return: the wind speed.
        """

        reference_speed = 10  # M_PER_S

        if unit == Unit.M_PER_S or unit == Unit.MS:
            speed = reference_speed
        if unit == Unit.KM_PER_H or unit == Unit.KMH:
            speed = reference_speed * 3.6
        elif unit == Unit.MILES_PER_H or unit == Unit.MPH:
            speed = reference_speed * 2.237
        elif unit == Unit.FT_PER_S or unit == Unit.FTS:
            speed = reference_speed * 3.28

        return speed

    def wind_direction(self, unit=Unit.DEG):
        """
        Returns the wind direction in the chosen unit in the range between 0 to 360 degrees.
        :param unit:  Unit in which the instrument should return the angle.
        :return: the angle.
        """

        hour = datetime.datetime.now().hour

        return 180 * math.sin(self._hourinradians(hour)) + 180

    def dew_point(self, unit=Unit.CELSIUS):
        """
        Some simulations ran on 'http://www.cactus2000.de/uk/unit/masshum.shtml' suggests that
        the dew point at 1.5mm Hg and low temperatures are very low, around -20 C.
        Here I'm using -10 C.

        :param unit:  Unit in which the instrument should return the temperature.
        :return: the angle.
        """

        temperature = -10  #CELSIUS

        if unit == Unit.FAHRENHEIT:
            temperature = self._celsius_to_fahrenheit(temperature)
        elif unit == Unit.KELVIN:
            temperature = self._celsius_to_kelvin(temperature)

        return temperature

    def pressure(self, unit=Unit.MM_HG):
        """
        Pressure at 1.5 atm
        :param unit:
        :return:
        """
        pressure_reference = 1140.  # MM_HG

        if unit == Unit.MM_HG:
            pressure = pressure_reference
        elif unit == Unit.M_BAR:
            pressure = pressure_reference*1.3333
        elif unit == Unit.TORR:
            pressure = pressure_reference  # for practical effects, MM_HG = TORR
        elif unit == Unit.ATM:
            pressure = pressure_reference * 1.315e-3
        elif unit == Unit.PA:
            pressure = pressure_reference * 133.322
        elif unit == Unit.PSI:
            pressure = pressure_reference * 19.336e-3



        return pressure

    def rain(self, unit=Unit.MM_PER_H):
        """
        For testing purposes, it never rains.
        :param unit:
        :return:
        """

        return 0.


if __name__ == '__main__':

    fws = FakeWeatherStation()

    print('Humidity: %.2f %%.' % fws.humidity())
    print('Temperature: %.2f C.' % fws.temperature())

    print('Wind Speed: %.2f m/s.' % fws.wind_speed())
    print('Wind Direction: %.2f deg.' % fws.wind_direction())
    print('Dew Point: %.2f C.' % fws.dew_point())
    print('Pressure: %.2f mmHg.' % fws.pressure())
    print('Rain: %.2f mm/h.' % fws.rain())
