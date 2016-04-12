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
from chimera.util.enum import Enum

FocuserFeature = Enum("TEMPERATURE_COMPENSATION",
                      "ENCODER",
                      "POSITION_FEEDBACK",
                      "CONTROLLABLE_X",
                      "CONTROLLABLE_Y",
                      "CONTROLLABLE_Z",
                      "CONTROLLABLE_U",
                      "CONTROLLABLE_V",
                      "CONTROLLABLE_W")

FocuserAxis = Enum("X", "Y", "Z", "U", "V", "W")

ControllableAxis = {FocuserFeature.CONTROLLABLE_X: FocuserAxis.X,
                    FocuserFeature.CONTROLLABLE_Y: FocuserAxis.Y,
                    FocuserFeature.CONTROLLABLE_Z: FocuserAxis.Z,
                    FocuserFeature.CONTROLLABLE_U: FocuserAxis.U,
                    FocuserFeature.CONTROLLABLE_V: FocuserAxis.V,
                    FocuserFeature.CONTROLLABLE_W: FocuserAxis.W,
                    }

AxisControllable = {FocuserAxis.X: FocuserFeature.CONTROLLABLE_X,
                    FocuserAxis.Y: FocuserFeature.CONTROLLABLE_Y,
                    FocuserAxis.Z: FocuserFeature.CONTROLLABLE_Z,
                    FocuserAxis.U: FocuserFeature.CONTROLLABLE_U,
                    FocuserAxis.V: FocuserFeature.CONTROLLABLE_V,
                    FocuserAxis.W: FocuserFeature.CONTROLLABLE_W,
                    }

class InvalidFocusPositionException(ChimeraException):
    """
    Represents an outside of boundaries Focuser error.
    """


class Focuser(Interface):
    """
    Instrument interface for an electromechanical focuser for
       astronomical telescopes.

       Two kinds of focusers are supported:

       - Encoder based: use optical encoder to move to exact
         positions.
       - DC pulse: just send a DC pulse to a motor and move
         to selected directions only (no position information).
    """

    __config__ = {"focuser_model": "Fake Focus Inc.",
                  "device": "/dev/ttyS1",
                  "model": "Fake Focuser Inc.",
                  "open_timeout": 10,
                  "move_timeout": 60}

    def moveIn(self, n, axis=FocuserAxis.Z):
        """
        Move the focuser IN by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Instruments use internal parameters to define the amount
        of movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move IN.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def moveOut(self, n, axis=FocuserAxis.Z):
        """
        Move the focuser OUT by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Instruments use internal parameters to define the amount
        of movement depending of the type of the encoder.

        Use L{moveTo} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move OUT.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def moveTo(self, position, axis=FocuserAxis.Z):
        """
        Move the focuser to the select position (if ENCODER_BASED
        supported).

        If the focuser doesn't support absolute position movement, use
        L{moveIn} and L{moveOut} to command the focuser.

        @type  position: int
        @param position: Position to move the focuser.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def getPosition(self, axis=FocuserAxis.Z):
        """
        Gets the current focuser position (if the POSITION_FEEDBACK
        supported).

        @raises NotImplementedError: When the focuser doesn't support
        position readout.

        @rtype   : int
        @return  : Current focuser position.
        """

    def getRange(self, axis=FocuserAxis.Z):
        """
        Gets the focuser total range
        @rtype: tuple
        @return: Start and end positions of the focuser (start, end)
        """

    def getTemperature(self):
        """
        Retusn the temperature of the focuser probe
        @rtype: float
        """

    def supports(self, feature=None):
        """
        Ask Focuser if it supports the given feature. Feature list
        is availble on L{FocuserFeature} enum.

        @param feature: Feature to inquire about
        @type  feature: FocusrFeature or str

        @returns: True is supported, False otherwise.
        @rtype: bool
        """
