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

from chimera.core.exceptions import ChimeraException


class InvalidFocusPositionException (ChimeraException):
    """
    Represents an outside of boundaries Focuser error.
    """


class IFocuser (Interface):
    """Instrument interface for an electromechanical focuser for
       astronomical telescopes.
       
       Two kinds of focuser are support (dependind of the driver):

       - Absolute encoder: use optical encoder to move to exact
         positions.
       - DC pulse: just send a DC pulse to a motor and move
         to selected directions only (no position information).
    """

    __config__ = {"driver": "/Fake/focus",
                  "model": "Fake Focus Inc.",}


    def moveIn (self, n):
        """
        Move the focuser IN by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Drivers use internal parameters to define the amount of
        movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move IN.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """


    def moveOut (self, n):
        """
        Move the focuser OUT by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Drivers use internal parameters to define the amount of
        movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move OUT.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def moveTo (self, position):
        """
        Move the focuser to the select position (if the driver support
        it).

        If the focuser doesn't support absolute position movement, use
        L{moveIn} and L{moveOut} to command the focuser.

        @type  position: int
        @param position: Position to move the focuser.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def getPosition (self):
        """
        Gets the current focuser position (if the driver support it).

        @raises NotImplementedError: When the focuser doesn't support
        position readout.

        @rtype   : int
        @return  : Current focuser position.
        """

