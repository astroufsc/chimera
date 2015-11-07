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

GuiderStatus = Enum("OK", "GUIDING", "OFF", "ERROR", "ABORTED")

class StarNotFoundException (ChimeraException):
    pass


class Autoguider (Interface):

    __config__ = {"site": '/Site/0',            # Telescope Site.
                  "telescope": "/Telescope/0",  # Telescope instrument that will be guided by the autoguider.
                  "camera": "/Camera/0",        # Guider camera instrument.
                  "filterwheel": None,          # Filter wheel instrument, if there is one.
                  "focuser": None,              # Guider camera focuser, if there is one.
                  "autofocus": None,            # Autofocus controller, if there is one.
                  "scheduler": None,            # Scheduler controller, if there is one.
                  "max_acquire_tries": 3,       # Number of tries to find a guiding star.
                  "max_fit_tries": 3}           # Number of tries to acquire the guide star offset before being lost.

    @event
    def offsetComplete(self, offset):
        """Raised after every offset is complete.
        """

    @event
    def guideStart(self, position):
        """Raised when a guider sequence starts.
        """

    @event
    def guideStop(self, state, msg=None):
        """Raised when a guider sequence stops.
        """
