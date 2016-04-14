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
from chimera.interfaces.weatherstation import WeatherStation, WeatherTemperature, WeatherHumidity, WeatherWind, \
    WeatherPressure, WeatherRain, WeatherTransparency
import astropy.units as units


class WeatherBase(ChimeraObject, WeatherStation):
    def __init__(self):
        ChimeraObject.__init__(self)

        self._supports = {}

    def _convert_units(self, value, unit_in, unit_out, equivalencies=None):
        if unit_in == unit_out:
            return value

        return (value * unit_in).to(unit_out, equivalencies).value

    def getMetadata(self, request):
        md = [('METMODEL', str(self['model']), 'Weather station Model')]

        # Temperature
        if self.features(WeatherTemperature):
            temp, dew = self.temperature(), self.dew_point()
            md += ([('METTEMP', str(temp.value), ('[%s] Weather station temperature' % temp.unit)),
                    ('METDEW', str(dew.value), ('[%s] Weather station dew point' % dew.unit))])

        # Humidity
        if self.features(WeatherHumidity):
            hum = self.humidity()
            md += [('METRH', str(hum.value), ('[%s] Weather station relative humidity' % hum.unit))]
        # Wind
        if self.features(WeatherWind):
            speed, direc = self.wind_speed(), self.wind_direction()
            md += [('METWINDS', str(speed.value), ('[%s] Weather station wind speed' % speed.unit)),
                   ('WINDDIR', str(direc.value), ('[%s] Weather station wind direction' % direc.unit))]

        # Pressure
        if self.features(WeatherPressure):
            press = self.pressure()
            md += [('METPRES', str(press.value), ('[%s] Weather station air pressure' % press.unit))]

        # Rain
        if self.features(WeatherRain):
            rate = self.rain_rate()
            md += [('METRAIN', str(rate.value), ('[%s] Weather station rain rate' % rate.unit))]

        # Sky Transparency
        if self.features(WeatherTransparency):
            transp = self.sky_transparency()
            md += [('METSKTR', str(transp.value), ('[%s] Weather station Sky Transparency' % transp.unit))]

        return md
