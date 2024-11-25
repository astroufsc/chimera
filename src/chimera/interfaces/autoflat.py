from chimera.core import SYSTEM_CONFIG_DIRECTORY
from chimera.interfaces.telescope import TelescopePierSide

__author__ = "kanaan"

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


class IAutoFlat(Interface):

    __config__ = {
        "telescope": "/Telescope/0",
        "dome": "/Dome/0",
        "camera": "/Camera/0",
        "filterwheel": "/FilterWheel/0",
        "site": "/Site/0",
    }

    def getFlats(self, filter_id, n_flats):
        """
        Takes sequence of flats, starts taking one frame to determine current level
        Then predicts next exposure time based on exponential decay of sky brightness
        Creates a list of sunZD, intensity.  It should have the right exponential behavior.
        If not exponential raise some flag about sky condition.
        """

    def getFlatLevel(self, filename, image):
        """
        Returns average level from image
        """

    @event
    def exposeComplete(self, filter_id, i_flat, expTime, level):
        """
        Called on exposuse completion
        """
