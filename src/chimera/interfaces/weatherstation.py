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
from chimera.util.enum import Enum

Unit = Enum("PERCENTUAL",  # Humidity

            "CELSIUS",    # Temperature, Dew point
            "KELVIN",
            "FAHRENHEIT",

            "M_PER_S",    # Wind Speed
            "KM_PER_H",
            "MILES_PER_H",
            "FT_PER_S",
            "MS",
            "KMH",
            "FTS",
            "MPH",

            "DEG",        # Wind Direction

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

class WeatherStation (Interface):
    """
    Instrument interface for weather stations

    """

    __config__ = {"device": None,

                  # "humidity_unit": units.pct,
                  # "temperature_unit": units.Celsius,
                  # "wind_unit": units.kilometer/units.hour,
                  # "wind_direction_unit": units.degree,
                  # "dew_point_unit": units.Celsius,
                  # "pressure_unit": units.cds.mmHg,
                  # "rain_unit": units.liter / units.hour,

                  # "humidity_unit": "PERCENTAGE",
                  # "temperature_unit": "CELSIUS",
                  # "wind_unit": "KM_H",
                  # "wind_direction_unit": "DEGREES",
                  # "dew_point_unit": "CELSIUS",
                  # "pressure_unit": "MM_HG",
                  # "rain_unit": "L_H",

                 "humidity_unit": Unit.MM_HG,
                  "temperature_unit": Unit.CELSIUS,
                  "wind_unit": Unit.KM_PER_H,
                  "dew_point_unit": Unit.CELSIUS,
                  "pressure_unit": Unit.PERCENTUAL,
                  "rain_unit": Unit.MM_PER_H,


                  "humidity_delta": 1,
                  "temperature_delta": 1,
                  "wind_delta": 1,
                  "dew_point_delta": 1,
                  "pressure_delta": 1,
                  }

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

    def wind_speed(self, unit_out=units.kilometer/units.hour):
        """
        Returns the wind speed in the chosen unit (Default: Meters per second).
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

    def pressure(self, unit_out=units.cds.mmHg):
        """
        Returns the pressure in the chosen unit (Default: mmHg).
        :param unit:  Unit in which the instrument should return the pressure.
        :return: the pressure.
        """
        pass

    def rain(self, unit_out=units.liter/units.hour):
        """
        Returns the precipitation rate in the chosen unit (Default: mm/H).
        :param unit:  Unit in which the instrument should return the precipitation rate.
        :return: the precipitation rate.
        """
        pass