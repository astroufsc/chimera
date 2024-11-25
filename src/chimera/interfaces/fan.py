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
from chimera.interfaces.switch import Switch, SwitchStatus, SwitchState
from chimera.util.enum import Enum

FanDirection = Enum("FORWARD", "REVERSE")
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
