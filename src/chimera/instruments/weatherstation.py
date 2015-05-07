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

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.weatherstation import WeatherStation, Unit


class WeatherBase(ChimeraObject, WeatherStation):
    def __init__(self):
        ChimeraObject.__init__(self)

        self._supports = {}

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            self.log.info("Invalid feature: %s" % str(feature))
            return False

    def humidity(self, deltaT=0, unit=Unit.PERCENTUAL):
        raise NotImplementedError()

    def temperature(self, deltaT=0, unit=Unit.CELSIUS):
        raise NotImplementedError()

    def wind_speed(self, deltaT=0, unit=Unit.M_PER_S):
        raise NotImplementedError()

    def wind_direction(self, deltaT=0, unit=Unit.DEG):
        raise NotImplementedError()

    def dew_point(self, deltaT=0, unit=Unit.CELSIUS):
        raise NotImplementedError()

    def pressure(self, deltaT=0, unit=Unit.MM_HG):
        raise NotImplementedError()

    def rain(self, deltaT=0, unit=Unit.MM_PER_H):
        raise NotImplementedError()

    def getMetadata(self, request):
        #TODO: Check if metadata parameter is implemented or not.
        return [('METMODEL', str(self['model']), 'Weather station Model'),
                ('METRH', str(self.humidity()), '[%] Weather station relative humidity'),
                ('METTEMP', str(self.temperature()), '[degC] Weather station temperature'),
                ('METWINDS', str(self.wind_speed()), '[m/s] Weather station wind speed'),
                ('WINDDIR',  str(self.wind_direction()), '[deg] Weather station wind direction'),
                ('METDEW',  str(self.dew_point()), '[degC] Weather station dew point'),
                ('METPRES', str(self.pressure()), '[hPa] Weather station air pressure'),
                ('METRAIN', str(self.pressure()), 'Weather station rain indicator'),
                ]