# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
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
    def set_intensity(self, intensity):
        """
        Sets the intensity of the calibration lamp.

        @param intensity: Desired intensity.
        @type  intensity: float
        """
        pass

    def get_intensity(self):
        """
        Return the current intensity level of the calibration lamp.

        Note that a intensity of 0 does not mean that the lamp is switched off and a intensity >0 does not mean
        that the lamp in switched on. This will be implementation dependent. The best way to check if a lamp is
        on or off is with the "is_switched_on" function.

        @return: Current intensity
        @rtype: float
        """
        pass

    def get_range(self):
        """
        Gets the dimmer total range
        @rtype: tuple
        @return: Start and end positions of the dimmer (start, end)
        """
        pass
