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

        return 25 * math.sin(self._hourinradians(hour) - math.pi/2) + 15

    def wind_speed(self, unit=Unit.M_PER_S):

        return 10

    def wind_direction(self, unit=Unit.DEG):
        return 90

    def dew_point(self, unit=Unit.CELSIUS):
        return 0

    def pressure(self, unit=Unit.MM_HG):
        """
        Pressure at 1.5 atm
        :param unit:
        :return:
        """
        return 1140.

    def rain(self, unit=Unit.MM_PER_H):

        return 0.


if __name__ == '__main__':

    fws = FakeWeatherStation()

    print('Humididy: %.2f %%.' % fws.humidity())
    print('Temperature: %.2f C.' % fws.temperature())

    print('Wind Speed: %.2f m/s.' % fws.wind_speed())
    print('Wind Direction: %.2f deg.' % fws.wind_direction())
    print('Dew Point: %.2f C.' % fws.dew_point())
    print('Pressure: %.2f mmHg.' % fws.
          pressure())
    print('Rain: %.2f mm/h.' % fws.rain())
