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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


from chimera.core.interface import Interface
from astropy import units
from astropy.units import cds
from collections import namedtuple


class WSValue(namedtuple('WSValue', 'time value unit')):
    """
    Named tuple that represents a measure
    """
    pass


class WeatherStation (Interface):
    """
    Instrument interface for weather stations

    """

    __config__ = {"device": None,           # weather station device
                  "model": "unknown",     # weather station model
                  }



    """
    Humidity units accepted by the interface.
    """
    __accepted_humidity_units__ = [
        units.pct
    ]

    """
    Temperature units accepted by the interface.
    """
    __accepted_temperature_units__ = [
        units.Celsius,
        units.Kelvin,
        units.imperial.deg_F
    ]

    """
    Speed units accepted by the interface.
    """
    __accepted_speed_units__ = [
        units.meter / units.second,
        units.kilometer / units.hour,
        units.imperial.mile / units.hour,
        units.imperial.foot / units.second,
    ]

    """
    Direction units accepted by the interface.
    """
    __accepted_direction_unit__ = [
        units.degree,
        units.radian
    ]

    """
    Pressure units accepted by the interface.
    """
    __accepted_pressures_unit__ = [
        units.cds.mmHg,
        units.bar,
        units.cds.atm,
        units.Pa]

    """
    Pressure units accepted by the interface.
    """
    __accepted_precipitation_unit__ = [
        units.imperial.inch/units.hour,
        units.millimeter/units.hour,
    ]

    def humidity(self, unit_out=units.pct):
        """
        Returns the 100% relative humidity (Default: Percentage).
        :param unit: Unit in which the instrument should return the humidity.
        :return: the humidity.
        """
        pass

    def temperature(self, unit_out=units.Celsius):
        """
        Returns the temperature in the chosen unit (Default: Celsius).
        :param unit:  Unit in which the instrument should return the temperature.
        :return: the temperature.
        """
        pass

    def wind_speed(self, unit_out=units.meter/units.second):
        """
        Returns the wind speed in the chosen unit (Default: meters per second).
        :param unit:  Unit in which the instrument should return the wind speed.
        :return: the wind speed.
        """
        pass

    def wind_direction(self, unit_out=units.degree):
        """
        Returns the wind direction in the chosen unit (Default: Degrees).
        :param unit:  Unit in which the instrument should return the wind direction.
        :return: the wind direction.
        """
        pass

    def dew_point(self, unit_out=units.Celsius):
        """
        Returns the dew point temperature in the chosen unit (Default: Celsius).
        :param unit:  Unit in which the instrument should return the dew point.
        :return: the dew point temperature.
        """
        pass

    def pressure(self, unit_out=units.Pa):
        """
        Returns the pressure in the chosen unit (Default: units.Pa).
        :param unit:  Unit in which the instrument should return the pressure.
        :return: the pressure.
        """
        pass

    def rain(self, unit_out=units.imperial.inch/units.hour):
        """
        Returns the precipitation rate in the chosen unit (Default: inch/h).
        :param unit:  Unit in which the instrument should return the precipitation rate.
        :return: the precipitation rate.
        """
        pass