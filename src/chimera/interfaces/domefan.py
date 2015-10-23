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
from chimera.core.event import event

from chimera.util.enum import Enum

FanStatus = Enum("RUNNING", "STOPPED", "ABORTED", "ERROR")
FanDirection = Enum("FORWARD", "REVERSE")


class DomeFan(Interface):
    """
    A Roll-off or classic dome.
    """

    __config__ = {"device": "Unknown",

                  "min_speed": 0.,
                  "max_speed": 600.,

                  "model": "Fake Domes Fan Inc.",
                  }

    def getRotation(self):
        '''
        Get fan current rotation speed.

        @return: Rotation speed in Hz
        @rtype: float
        '''

    def setRotation(self, freq):
        '''
        Set fan rotation speed.

        @return: Nothing
        @rtype:

        '''

    def getDirection(self):
        '''
        Get fan rotation direction.

        @return: Fan direction
        @rtype: Enum{FanDirection}

        '''

    def setDirection(self, direction):
        '''
        Set fan rotation direction.

        @return: Nothing
        @rtype:

        '''

    def startFan(self):
        '''
        Start fan.

        @return: True if succeeded, False otherwise
        @rtype: bool

        '''

    def stopFan(self):
        '''
        Stop fan.

        @return: True if succeeded, False otherwise
        @rtype: bool

        '''

    def isFanRunning(self):
        """
        Ask if the fan is running right now.

        @return: True if the fan is running, False otherwise.
        @rtype: bool
        """

    def status(self):
        """

        @return: Fan current status
        @rtype: Enum{FanStatus}
        """


    @event
    def fanStarted(self):
        '''
        Indicates that fan has started

        '''

    @event
    def fanStopped(self):
        '''
        Indicates that fan has stopped

        '''
