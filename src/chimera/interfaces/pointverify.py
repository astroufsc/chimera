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
from chimera.core.exceptions import ChimeraException


class CantPointScopeException(ChimeraException):
    pass


class CanSetScopeButNotThisField(ChimeraException):
    pass


class CantSetScopeException(ChimeraException):
    pass


Target = Enum("CURRENT", "AUTO")


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

    def checkPointing(self, n_fields):
        """
        Check pointing choosing field and using default exposure time
        """

    @event
    def pointComplete(self, position, star, frame):
        """Raised after every step in the focus sequence with
        information about the last step.
        """
