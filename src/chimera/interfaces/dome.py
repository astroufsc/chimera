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
from chimera.core.exceptions import ChimeraException

from chimera.util.enum import Enum
from chimera.util.coord import Coord


__all__ = ['Mode',
           'Type',
           'Dome',
           'InvalidDomePositionException']


Mode = Enum("Stand", "Track")
Style = Enum("Rolloff", "Classic", "Other")
DomeStatus = Enum("OK", "ABORTED")


class InvalidDomePositionException(ChimeraException):
    """
    Raised when trying to slew to an invalid azimuth angle.
    """


class Dome(Interface):
    """
    A Roll-off or classic dome.
    """

    __config__ = {"device": "/dev/ttyS1",
                  "telescope": "/Telescope/0",
                  "mode": Mode.Stand,

                  "model": "Fake Domes Inc.",
                  "style": Style.Classic,

                  'park_position': Coord.fromD(155),
                  'park_on_shutdown': False,
                  'close_on_shutdown': False,

                  "az_resolution": 2,  # dome position resolution in degrees
                  "slew_timeout": 120,
                  "abort_timeout": 60,
                  "init_timeout": 5,
                  "open_timeout": 20,
                  "close_timeout": 20}

    def stand(self):
        """
        Tells the Dome to stand and only move when asked to.

        @rtype: None
        """

    def track(self):
        """
        Tells the Dome to track the telescope azimuth. Dome will use
        the telescope given in 'telescope' config parameter.

        @rtype: None
        """

    def syncWithTel(self):
        """
        If dome was in Track mode, sync dome position with current scope position.

        @rtype: None
        """

    def isSyncWithTel(self):
        """
        If dome was in Track mode, returns wether the dome slit is synchronized with telescope azimuth.

        @rtype: bool
        """

    def getMode(self):
        """
        Get the current Dome mode, Stand or Track, currently.

        @return: Dome's current mode.
        @rtype: Mode
        """

    def slewToAz(self, az):
        """
        Slew to the given Azimuth.

        @param az: Azimuth in degrees. Can be anything
        L{Coord.fromDMS} can accept.
        @type az: Coord, int or float

        @raises InvalidDomePositionException: When the request Azimuth
        is unreachable.

        @rtype: None
        """

    def isSlewing(self):
        """
        Ask if the dome is slewing right now.

        @return: True if the dome is slewing, False otherwise.
        @rtype: bool
        """

    def abortSlew(self):
        """
        Try to abort the current slew.

        @return: False if slew couldn't be aborted, True otherwise.
        @rtype: bool
        """

    def openSlit(self):
        """
        Open the dome slit.

        @rtype: None
        """

    def closeSlit(self):
        """
        Close the dome slit.

        @rtype: None
        """

    def isSlitOpen(self):
        """
        Ask the dome if the slit is opened.

        @return: True when open, False otherwise.
        @rtype: bool
        """

    def lightsOn(self):
        """
        Ask the dome to turn on flat lights, if any.
        @return: None
        @rtype: None
        """

    def lightsOff(self):
        """
        Ask the dome to turn off flat lights, if any.
        @return: None
        @rtype: None
        """

    def getAz(self):
        """
        Get the current dome Azimuth (Az)

        @return: Dome's current Az (decimal degrees)
        @rtype: float
        """

    @event
    def syncBegin(self):
        """
        Indicates that the dome was asked and is starting to sync with the telescope (if any).
        """

    @event
    def syncComplete(self):
        """
        Indicates that the dome was asked and finished the sync with the telescope (if any).
        """

    @event
    def slewBegin(self, position):
        """
        Indicates that the a new slew operation started.

        @param position: The dome current position when the slew started
        @type  position: Coord
        """

    @event
    def slewComplete(self, position, status):
        """
        Indicates that the last slew operation finished (with or
        without success, check L{status} field for more information.).

        @param position: The dome current position when the slew finished in
                         decimal degrees.
        @type  position: Coord

        @param status: Status of the slew command
        @type  status: L{DomeStatus}
        """

    @event
    def slitOpened(self, az):
        """
        Indicates that the slit was just opened

        @param az: The azimuth when the slit opend
        @type  az: Coord
        """
    @event
    def slitClosed(self, az):
        """
        Indicates that the slit was just closed.

        @param az: The azimuth when the slit closed.
        @type  az: Coord
        """
