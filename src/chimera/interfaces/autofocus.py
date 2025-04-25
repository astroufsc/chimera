# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.core.event import event

# from chimera.util.enum import Enum
from chimera.core.exceptions import ChimeraException


class StarNotFoundException(ChimeraException):
    pass


class FocusNotFoundException(ChimeraException):
    pass


class Autofocus(Interface):

    __config__ = {
        "camera": "/Camera/0",
        "filterwheel": "/FilterWheel/0",
        "focuser": "/Focuser/0",
        "max_tries": 3,
    }

    def focus(
        self,
        filter=None,
        exptime=None,
        binning=None,
        window=None,
        start=2000,
        end=6000,
        step=500,
        minmax=None,
        debug=False,
    ):
        """
        Focus
        """

    @event
    def step_complete(self, position, star, frame):
        """Raised after every step in the focus sequence with
        information about the last step.
        """
