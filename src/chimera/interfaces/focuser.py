# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.core.exceptions import ChimeraException
from chimera.util.enum import Enum


class FocuserFeature(Enum):
    TEMPERATURE_COMPENSATION = "TEMPERATURE_COMPENSATION"
    ENCODER = "ENCODER"
    POSITION_FEEDBACK = "POSITION_FEEDBACK"
    CONTROLLABLE_X = "CONTROLLABLE_X"
    CONTROLLABLE_Y = "CONTROLLABLE_Y"
    CONTROLLABLE_Z = "CONTROLLABLE_Z"
    CONTROLLABLE_U = "CONTROLLABLE_U"
    CONTROLLABLE_V = "CONTROLLABLE_V"
    CONTROLLABLE_W = "CONTROLLABLE_W"


class FocuserAxis(Enum):
    X = "X"
    Y = "Y"
    Z = "Z"
    U = "U"
    V = "V"
    W = "W"


ControllableAxis = {
    FocuserFeature.CONTROLLABLE_X: FocuserAxis.X,
    FocuserFeature.CONTROLLABLE_Y: FocuserAxis.Y,
    FocuserFeature.CONTROLLABLE_Z: FocuserAxis.Z,
    FocuserFeature.CONTROLLABLE_U: FocuserAxis.U,
    FocuserFeature.CONTROLLABLE_V: FocuserAxis.V,
    FocuserFeature.CONTROLLABLE_W: FocuserAxis.W,
}

AxisControllable = {
    FocuserAxis.X: FocuserFeature.CONTROLLABLE_X,
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

    __config__ = {
        "focuser_model": "Fake Focus Inc.",
        "device": "/dev/ttyS1",
        "model": "Fake Focuser Inc.",
        "open_timeout": 10,
        "move_timeout": 60,
    }

    def move_in(self, n, axis=FocuserAxis.Z):
        """
        Move the focuser IN by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Instruments use internal parameters to define the amount
        of movement depending of the type of the encoder.

        Use L{move_to} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move IN.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def move_out(self, n, axis=FocuserAxis.Z):
        """
        Move the focuser OUT by n steps. Steps could be absolute units
        (for focuser with absolute encoders) or just a pulse of
        time. Instruments use internal parameters to define the amount
        of movement depending of the type of the encoder.

        Use L{move_to} to move to exact positions (If the focuser
        support it).

        @type  n: int
        @param n: Number of steps to move OUT.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def move_to(self, position, axis=FocuserAxis.Z):
        """
        Move the focuser to the select position (if ENCODER_BASED
        supported).

        If the focuser doesn't support absolute position movement, use
        L{move_in} and L{move_out} to command the focuser.

        @type  position: int
        @param position: Position to move the focuser.

        @raises InvalidFocusPositionException: When the request
        movement couldn't be executed.

        @rtype   : None
        """

    def get_position(self, axis=FocuserAxis.Z):
        """
        Gets the current focuser position (if the POSITION_FEEDBACK
        supported).

        @raises NotImplementedError: When the focuser doesn't support
        position readout.

        @rtype   : int
        @return  : Current focuser position.
        """

    def get_range(self, axis=FocuserAxis.Z):
        """
        Gets the focuser total range
        @rtype: tuple
        @return: Start and end positions of the focuser (start, end)
        """

    def get_temperature(self):
        """
        Returns the temperature of the focuser probe
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
