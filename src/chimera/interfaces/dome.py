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


from chimera.core.interface  import Interface
from chimera.core.event      import event
from chimera.core.exceptions import ChimeraException

from chimera.util.enum import Enum



__all__ = ['Mode',
           'Type',
           'IDome',
           'InvalidDomePositionException']


Mode = Enum("Stand", "Track")
Type = Enum("Rolloff", "Classic", "Other")


class InvalidDomePositionException (ChimeraException):
    """
    Raised when trying to slew to an invalid azimuth angle.
    """


class IDome (Interface):
    """A Roll-off or classic dome.
    """

    __config__ = {"driver"   : "/DomeLNA40cm/dome",
                  "telescope": "/Telescope/0",
                  "mode"     : Mode.Stand,

                  "model"    : "Fake Domes Inc.",
                  "type"     : Type.Classic,}


    def stand (self):
        """
        Tells the Dome to stand and only move when asked to.

        @rtype: None
        """

    def track (self):
        """
        Tells the Dome to track the telescope azimuth. Dome will use
        the telescope given in 'telescope' config parameter.

        @rtype: None
        """

    def getMode (self):
        """
        Get the current Dome mode, Stand or Track, currently.

        @return: Dome's current mode.
        @rtype: Mode
        """

    def slewToAz (self, az):
        """Slew to the given Azimuth.

        @param az: Azimuth in degrees. Can be anything
        L{Coord.fromDMS} can accept.
        @type az: Coord, int or float

        @raises InvalidDomePositionException: When the request Azimuth
        is unreachable.

        @rtype: None
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

    def openSlit (self):
        """Open the dome slit.

        @rtype: None
        """

    def closeSlit (self):
        """Close the dome slit.

        @rtype: None
        """

    def isSlitOpen (self):
        """Ask the dome if the slit is opened.

        @return: True when open, False otherwise.
        @rtype: bool
        """

    def getAz (self):
        """Get the current dome Azimuth (Az)

        @return: Dome's current Az (decimal degrees)
        @rtype: float
        """

    @event
    def slewBegin (self, position):
        """Indicates that the a new slew operation started.

        @param position: The dome current position when the slew started
        @type  position: Coord
        """

    @event
    def slewComplete (self, position):
        """Indicates that the last slew operation finished (with or without success).

        @param position: The dome current position when the slew finished in decimal degrees.
        @type  position: Coord
        """

    @event
    def abortComplete (self, position):
        """Indicates that the last slew operation was aborted.

        @param position: The dome position when the slew aborted in decimal degrees).
        @type  position: Coord
        """

    @event
    def slitOpened (self, az):
        """Indicates that the slit was just opened

        @param az: The azimuth when the slit opend
        @type  az: Coord
        """
    @event
    def slitClosed (self, az):
        """Indicates that the slit was just closed.

        @param az: The azimuth when the slit closed.
        @type  az: Coord
        """
