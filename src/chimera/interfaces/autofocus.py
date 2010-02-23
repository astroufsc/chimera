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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


from chimera.core.interface import Interface
from chimera.core.event import event

from chimera.util.enum import Enum
from chimera.core.exceptions import ChimeraException


class StarNotFoundException (ChimeraException):
    pass

class FocusNotFoundException (ChimeraException):
    pass

class Autofocus (Interface):

    __config__ = {"camera"             : "/Camera/0",
                  "filterwheel"        : "/FilterWheel/0",
                  "focuser"            : "/Focuser/0",
                  "max_tries"          : 3}

    def focus (self, filter=None, exptime=None, binning=None, window=None,
               start=2000, end=6000, step=500,
               minmax=None, debug=False):
        """
        Focus
        """

    @event
    def stepComplete (self, position, star, frame):
        """Raised after every step in the focus sequence with
        information about the last step.
        """

