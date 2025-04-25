# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.core.event import event

from chimera.util.enum import Enum
from chimera.core.exceptions import ChimeraException


class CantPointScopeException(ChimeraException):
    pass


class CanSetScopeButNotThisField(ChimeraException):
    pass


class CantSetScopeException(ChimeraException):
    pass


class Target(Enum):
    CURRENT = "CURRENT"
    AUTO = "AUTO"


class PointVerify(Interface):

    __config__ = {
        "camera": "/Camera/0",  # Camera attached to the telescope.
        "filterwheel": "/FilterWheel/0",  # Filterwheel, if exists.
        "telescope": "/Telescope/0",  # Telescope to verify pointing.
        "exptime": 10.0,  # Exposure time.
        "filter": "R",  # Filter to expose.
        "max_fields": 100,  # Maximum number of Landlodt fields to use.
        "max_tries": 5,  # Maximum number of tries to point the telescope correctly.
        "dec_tolerance": 0.0167,  # Maximum declination error tolerance (degrees).
        "ra_tolerance": 0.0167,  # Maximum right ascension error tolerance (degrees).
    }

    def check_pointing(self, n_fields):
        """
        Check pointing choosing field and using default exposure time
        """

    @event
    def point_complete(self, position, star, frame):
        """Raised after every step in the focus sequence with
        information about the last step.
        """
