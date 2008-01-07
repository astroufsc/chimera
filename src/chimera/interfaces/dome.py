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


class IDome (Interface):
    """A Roll-off or classic dome.
    """

    __options__ = {"driver"   : "/DomeLNA40cm/dome",
                   "telescope": "/Telescope/0",
                   "mode"     : ["stand", "track"],

                   "model"    : "Fake Domes Inc.",
                   "type"     : ["Rolloff", "Classic", "Othter"],
                   }

    
    def sletToAz (self, az):
        """Slew to the given Azimuth.

        @param az: Azimuth in degrees.
        @type  az: int or float

        @return: False if slew failed, True otherwise
        @rtype: bool
        """

    def isSlewing (self):
        """Ask if the dome is slewing right now.

        @return: True if the dome is slewing, False otherwise.
        @rtype: bool
        """

    def abortSlew (self):
        """Try to abort the current slew.

        @return: False if slew couldn't be aborted, True otherwise.
        @rtype: bool
        """

    def getAz (self):
        """Get the current dome Azimuth (Az)

        @return: Dome's current Az (decimal degrees)
        @rtype: float
        """

    @event
    def slewComplete (self, position):
        """Indicates that the last slew operation finished (with or without success).

        @param position: The dome current position when the slew finished in decimal degrees.
        @type  position: float
        """

    @event
    def abortComplete (self, position):
        """Indicates that the last slew operation was aborted.

        @param position: The dome position when the slew aborted in decimal degrees).
        @type  position: float
        """
