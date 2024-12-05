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
from chimera.core.exceptions import ChimeraException
from chimera.interfaces.switch import Switch


class IntensityOutOfRangeException(ChimeraException):
    """
    Raise when the requested lamp intensity is out of range.
    """

    pass


class Lamp(Interface):
    """
    Interface to calibration lamps.
    """

    __config__ = {
        "device": None,
        "switch_timeout": None,  # Maximum number of seconds to wait for lamp to switch on
        "dome_az": None,  # Azimuth of the dome when taking a calibration image (flat field)
        "telescope_alt": None,  # Altitude of the telescope when taking a calibration image
        "telescope_az": None,  # Azimuth of the telescope when taking a calibration image
    }


class LampSwitch(Switch):
    """
    Inherited from Switch
    """


class LampDimmer(Lamp):
    def setIntensity(self, intensity):
        """
        Sets the intensity of the calibration lamp.

        @param intensity: Desired intensity.
        @type  intensity: float
        """
        pass

    def getIntensity(self):
        """
        Return the current intensity level of the calibration lamp.

        Note that a intensity of 0 does not mean that the lamp is switched off and a intensity >0 does not mean
        that the lamp in switched on. This will be implementation dependent. The best way to check if a lamp is
        on or off is with the "isSwitchedOn" function.

        @return: Current intensity
        @rtype: float
        """
        pass

    def getRange(self):
        """
        Gets the dimmer total range
        @rtype: tuple
        @return: Start and end positions of the dimmer (start, end)
        """
        pass
