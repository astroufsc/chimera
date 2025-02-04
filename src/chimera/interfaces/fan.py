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


class FanControllabeSpeed(Fan):
    """
    Fans with controllable speeds.
    """

    def getRotation(self):
        """
        Get fan current rotation speed.

        @return: Rotation speed in Hz
        @rtype: float
        """

    def setRotation(self, freq):
        """
        Set fan rotation speed.

        @return: Nothing
        @rtype:

        """

    def getRange(self):
        """
        Gets the fan valid speed range.

        @rtype: tuple
        @return: Minimum and maximum fan speed (min, max).
        """


class FanControllabeDirection(Fan):
    """
    Fans with controllable direction.
    """

    def getDirection(self):
        """
        Get fan rotation direction.

        @return: Fan direction
        @rtype: Enum{FanDirection}

        """

    def setDirection(self, direction):
        """
        Set fan rotation direction.

        @return: Nothing
        @rtype:

        """
