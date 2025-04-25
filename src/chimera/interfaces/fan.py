# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.interfaces.switch import Switch, SwitchStatus, SwitchState
from chimera.util.enum import Enum


class FanDirection(Enum):
    FORWARD = "FORWARD"
    REVERSE = "REVERSE"


FanStatus = SwitchStatus


class Fan(Interface):
    """
    Basic fan interface.
    """

    __config__ = {
        "device": None,
        "model": "Unknown",
    }


class FanControl(Switch):
    """
    Class for starting/stopping fans.
    All methods are inherited from Switch
    """


class FanState(SwitchState):
    """
    Class for fans status
    All methods are inherited from Switch
    """


class FanControllableSpeed(Fan):
    """
    Fans with controllable speeds.
    """

    def get_rotation(self):
        """
        Get fan current rotation speed.

        @return: Rotation speed in Hz
        @rtype: float
        """

    def set_rotation(self, freq):
        """
        Set fan rotation speed.

        @return: Nothing
        @rtype:

        """

    def get_range(self):
        """
        Gets the fan valid speed range.

        @rtype: tuple
        @return: Minimum and maximum fan speed (min, max).
        """


class FanControllableDirection(Fan):
    """
    Fans with controllable direction.
    """

    def get_direction(self):
        """
        Get fan rotation direction.

        @return: Fan direction
        @rtype: Enum{FanDirection}

        """

    def set_direction(self, direction):
        """
        Set fan rotation direction.

        @return: Nothing
        @rtype:

        """
