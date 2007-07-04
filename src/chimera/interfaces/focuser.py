#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

class IFocuser (Interface):
    """
    Instrument interface for an electromechanical focuser for astronomical telescopes.
    
    Two kinds of focuser are support (dependind of the driver):

     - Absolute encoder: use optical encoder to move to exact positions.
     - DC pulse: just send a DC pulse to a motor and move to selected directions only (no position information).
    """

    __options__ = {"driver": "/Fake/focus"}

    def moveIn (self, n):
        """
        Move the focuser IN by n steps. Steps could be absolute units (for focuser with absolute
        encoders) or just a pulse of time. Drivers use internal parameters to define the amount of
        movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser support it).

        @type  n: int
        @param n: Number of steps to move IN.

        @rtype   : bool
        @return  : True if the focuser could move the select number of steps. False otherwise.
        """


    def moveOut (self, n):
        """
        Move the focuser OUT by n steps. Steps could be absolute units (for focuser with absolute
        encoders) or just a pulse of time. Drivers use internal parameters to define the amount of
        movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser support it).

        @type  n: int
        @param n: Number of steps to move OUT.

        @rtype   : bool
        @return  : True if the focuser could move the select number of steps. False otherwise.
        """

    def moveTo (self, position):
        """
        Move the focuser to the select position (if the driver support it).

        If the focuser doesn't support absolute position movement, use L{moveIn}
        and L{moveOut} to command the focuser.

        @type  position: int
        @param position: Position to move the focuser.

        @rtype   : bool
        @return  : True if the focuser could move the select position. False otherwise.
        """

    def getPosition (self):
        """
        Gets the current focuser position (if the driver support it).

        @rtype   : int
        @return  : Current focuser position or -1 if the driver don't support position readout.
        """

        
class IFocuserDriver (Interface):
    """
    Driver for an Electromechanical focuser.

    Both DC pulse and absolute encoder focuser could be used. Implementation takes care of the diferences
    between these kind of focusers.
    """

    __options__ = {"pulse_in_multiplier": 100,
                   "pulse_out_multiplier": 100}
                 
    def moveIn (self, n):
        """
        Move the focuser IN by n steps.

        Driver should interpret n as whatever it support (time pulse or absolute encoder positions).
        if only time pulse is available, driver must use L{pulse_in_multiplier} as a multiple to determine
        how much time the focuser will move IN. L{pulse_in_multiplier} and n will be in miliseconds.

        @type  n: int
        @param n: Number of steps to move IN.

        @rtype   : bool
        @return  : True if the focuser could move the select number of steps. False otherwise.
        """


    def moveOut (self, n):
        """
        Move the focuser OUT by n steps.

        Driver should interpret n as whatever it support (time pulse or absolute encoder positions).
        if only time pulse is available, driver must use L{pulse_out_multiplier} as a multiple to determine
        how much time the focuser will move OUT. L{pulse_out_multiplier} and n will be in miliseconds.

        @type  n: int
        @param n: Number of steps to move OUT.

        @rtype   : bool
        @return  : True if the focuser could move the select number of steps. False otherwise.
        """

    def moveTo (self, position):
        """
        Move the focuser to the select position.

        If the focuser doesn't support absolute position movement, it MUST return False.

        @type  position: int
        @param position: Position to move the focuser.

        @rtype   : bool
        @return  : True if the focuser could move the select position. False otherwise.
        """

    def getPosition (self):
        """
        Gets the current focuser position.

        If the driver doesn't support position readout it MUST return -1.

        @rtype   : int
        @return  : Current focuser position or -1 if the driver don't support position readout.
        """
        
    
