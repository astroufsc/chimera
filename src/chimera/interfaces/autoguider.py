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

    __config__ = {"telescope": "/Telescope/0",
                  "camera": "/Camera/0",
                  "filterwheel": "/FilterWheel/0",
                  "focuser": "/Focuser/0",
                  "autofocus": "/Autofocus/0",
                  "point_verify": "/PointVerify/0",
                  'site': '/Site/0',
                  "max_tries": 3,
                  "Noffset": 0.,
                  "Eoffset": 0.}

    @event
    def offsetComplete(self, offset):
        """Raised after every offset is complete.
        """

    @event
    def guideStart(self, position):
        """Raised when a guider sequence starts.
        """

    @event
    def guideStopped(self, state, msg=None):
        """Raised when a guider sequence stops.
        """
