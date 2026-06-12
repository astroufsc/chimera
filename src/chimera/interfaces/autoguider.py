# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class GuiderStatus(Enum):
    OK = "OK"
    GUIDING = "GUIDING"
    OFF = "OFF"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class StarNotFoundException(ChimeraException):
    pass


class Autoguider(Interface):
    __config__ = {
        "site": "/Site/0",  # Telescope Site.
        "telescope": "/Telescope/0",  # Telescope instrument that will be guided by the autoguider.
        "camera": "/Camera/0",  # Guider camera instrument.
        "max_acquire_tries": 3,  # Number of tries to find a guiding star.
        "max_fit_tries": 3,
    }  # Number of tries to acquire the guide star offset before being lost.

    def find_star(self):
        """Attempts to find a guide star in the current field of view.

        Raises:
            StarNotFoundException: If no star is found.
        """

        raise NotImplementedError()

    @event
    def offset_complete(self, offset):
        """Raised after every offset is complete."""

    @event
    def guide_start(self, position):
        """Raised when a guider sequence starts."""

    @event
    def guide_stop(self, state, msg=None):
        """Raised when a guider sequence stops."""

    @event
    def star_acquired(self, position):
        """Raised when the guide star is acquired."""

    @event
    def star_lost(self):
        """Raised when the guide star is lost."""
