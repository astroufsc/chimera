# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.core.exceptions import ChimeraException

from chimera.util.enum import Enum
from chimera.util.coord import Coord


__all__ = ["Mode", "Style", "Dome", "InvalidDomePositionException"]


class Mode(Enum):
    Stand = "Stand"
    Track = "Track"


class Style(Enum):
    Rolloff = "Rolloff"
    Classic = "Classic"
    Other = "Other"


class DomeStatus(Enum):
    OK = "OK"
    ABORTED = "ABORTED"


class InvalidDomePositionException(ChimeraException):
    """
    Raised when trying to slew to an invalid azimuth angle.
    """


class Dome(Interface):
    """
    A Roll-off or classic dome.
    """

    __config__ = {
        "device": None,
        "telescope": "/Telescope/0",
        "mode": Mode.Stand,
        "model": "Fake Domes Inc.",
        "style": Style.Classic,
        "park_position": Coord.fromD(155),
        "park_on_shutdown": False,
        "close_on_shutdown": False,
        "az_resolution": 2,  # dome position resolution in degrees
        "slew_timeout": 120,
        "abort_timeout": 60,
        "init_timeout": 5,
        "open_timeout": 20,
        "close_timeout": 20,
        "fans": [],  # list of fans of the dome, i.e.: fans: ['/FakeFan/fake1', '/FakeFan/fake2']
        "lamps": [],  # list of lamps of the dome, i.e.: lamps: ['/FakeLamp/fake1']
    }


class DomeSlew(Dome):
    """Basic Interface for rotating observatory Domes."""

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


class DomeSlit(Dome):
    """
    Dome with Slit
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


class DomeFlap(Dome):
    """
    Dome with Slit
    """

    def openFlap(self):
        """
        Open the dome flap.

        @rtype: None
        """

    def closeFlap(self):
        """
        Close the dome flap.

        @rtype: None
        """

    def isFlapOpen(self):
        """
        Ask the dome if the flap is open.

        @return: True when open, False otherwise.
        @rtype: bool
        """

    @event
    def flapOpened(self, az):
        """
        Indicates that the flap was just opened

        @param az: The azimuth when the flap opend
        @type  az: Coord
        """

    @event
    def flapClosed(self, az):
        """
        Indicates that the flap was just closed.

        @param az: The azimuth when the flap closed.
        @type  az: Coord
        """


class DomeSync(Dome):
    """
    Synchronism operations with a chosen telescope.
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

    def getAz(self):
        """
        Get the current dome Azimuth (Az)

        @return: Dome's current Az (decimal degrees)
        @rtype: float
        """
