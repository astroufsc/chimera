#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

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


from chimera.core.interface import Interface
from chimera.core.event     import event
from chimera.util.enum      import Enum


Unit = Enum ("PERCENTUAL", # Humidity
             
             "CELSIUS",    # Temperature, Dew point
             "KELVIN",
             "FAHRENHEIT",

             "M_PER_S",    # Wind
             "KM_PER_H",
             "MILES_PER_H",
             "FT_PER_S",
             "MS",
             "KMH",
             "FTS",
             "MPH",

             "M_BAR",      # Pressure
             "MM_HG",
             "TORR",
             "ATM",
             "PA",
             "PSI",

             "MM_PER_H",       # Rain
             "CM_PER_H",
             "FT_PER_H",
             )


class IWeatherStation (Interface):

    __config__ = {"driver": "/Fake/weather",
                  
                  "humidity_unit"   : Unit.MM_HG,
                  "temperature_unit": Unit.CELSIUS,
                  "wind_unit"       : Unit.KM_PER_H,
                  "dew_point_unit"  : Unit.CELSIUS,
                  "pressure_unit"   : Unit.PERCENTUAL,
                  "rain_unit"       : Unit.MM_PER_H,
                  
                  "humidity_delta"   : 1,
                  "temperature_delta": 1,
                  "wind_delta"       : 1,
                  "dew_point_delta"  : 1,
                  "pressure_delta"   : 1,
                  "rain_delta"       : 1,
                  }

    def humididy (self, deltaT=0, unit=Unit.PERCENTUAL):
        pass

    def temperature (self, deltaT=0, unit=Unit.CELSIUS):
        pass

    def wind (self, deltaT=0, unit=Unit.M_PER_S):
        pass

    def dewPoint (self, deltaT=0, unit=Unit.CELSIUS):
        pass

    def pressure (self, deltaT=0, unit=Unit.MM_HG):
        pass

    def rain (self, deltaT=0, unit=Unit.MM_PER_H):
        pass

    @event
    def humidiyChange (self, humidity, unit, delta):
        pass

    @event
    def temperatureChange (self, temperature, unit, delta):
        pass

    @event
    def windChange (self, wind, unit, delta):
        pass

    @event
    def dewPointChange (self, dewPoint, unit, delta):
        pass

    @event
    def pressureChange (self, pressure, unit, delta):
        pass

    @event
    def rain (self, rain, unit, delta):
        pass
