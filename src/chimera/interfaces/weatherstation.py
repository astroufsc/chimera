#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from uts.core.interface import Interface

class IWeatherStation(Interface):

    # properties
    _humididy = 0.0
    _temperature = 0.0
    _wind = [0.0, 1]
    _dewPoint = 0.0
    _pressure = 0.0
    _rain = [0.0, 0.0]

    # events
    def humididy(self, humidity):
        pass
    
    def temperature(self, temp):
        pass
    
    def wind(self, wind):
        pass
    
    def dewPoint(self, dew):
        pass

    def pressure(self, pressure):
        pass
    
    def rain(self, rain):
        pass
