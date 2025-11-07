# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class CantPointScopeException(ChimeraException):
    pass


class CanSetScopeButNotThisField(ChimeraException):
    pass


class CantSetScopeException(ChimeraException):
    pass


class Target(Enum):
    CURRENT = "CURRENT"
    AUTO = "AUTO"


class IAutoFlat(Interface):
    __config__ = {
        "telescope": "/Telescope/0",
        "dome": "/Dome/0",
        "camera": "/Camera/0",
        "filterwheel": "/FilterWheel/0",
        "site": "/Site/0",
    }

    def get_flats(self, filter_id, n_flats):
        """
        Takes sequence of flats, starts taking one frame to determine current level
        Then predicts next exposure time based on exponential decay of sky brightness
        Creates a list of sunZD, intensity.  It should have the right exponential behavior.
        If not exponential raise some flag about sky condition.
        """

    def get_flat_level(self, filename, image):
        """
        Returns average level from image
        """

    @event
    def expose_complete(self, filter_id, i_flat, exp_time, level):
        """
        Called on exposuse completion
        """
