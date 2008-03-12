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
from chimera.core.event import event


class IFocuserDriver (Interface):
    """
    Driver for an Electromechanical focuser.

    Both DC pulse and absolute encoder focuser could be
    used. Implementation takes care of the diferences between these
    kind of focusers.
    """

    __config__ = {"device": "/dev/ttyS1",
                  "open_timeout": 10,
                  "move_timeout": 60,
                  "max_position": 7000,
                  "min_position": 0,
                  "pulse_in_multiplier": 100,
                  "pulse_out_multiplier": 100}
                 
    def moveIn (self, n):
        """
        Move the focuser IN by n steps.

        Driver should interpret n as whatever it support (time pulse
        or absolute encoder positions).  if only time pulse is
        available, driver must use pulse_in_multiplier as a multiple
        to determine how much time the focuser will move
        IN. pulse_in_multiplier and n will be in miliseconds.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  n: int
        @param n: Number of steps to move IN.

        @rtype   : None
        """


    def moveOut (self, n):
        """
        Move the focuser OUT by n steps.

        Driver should interpret n as whatever it support (time pulse
        or absolute encoder positions).  if only time pulse is
        available, driver must use pulse_out_multiplier as a multiple
        to determine how much time the focuser will move
        OUT. pulse_out_multiplier and n will be in miliseconds.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  n: int
        @param n: Number of steps to move OUT.

        @rtype   : None
        """

    def moveTo (self, position):
        """
        Move the focuser to the select position.

        If the focuser doesn't support absolute position movement, it
        MUST return False.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  position: int
        @param position: Position to move the focuser.

        @rtype   : None
        """

    def getPosition (self):
        """
        Gets the current focuser position.

        @note: If the driver doesn't support position readout it MUST
        raise NotImplementedError.

        @rtype   : int
        @return  : Current focuser position.
        """
        
    
