# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from dataclasses import dataclass, field
from typing import Any

from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum

__all__ = [
    "Mode",
    "Style",
    "DomeStatus",
    "Dome",
    "DomeSlew",
    "DomeSlit",
    "DomeFlap",
    "DomeWindScreen",
    "DomeSync",
    "InvalidDomePositionException",
]


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


@dataclass
class DomeConfig:
    device: str | None = None
    telescope: str | None = "/Telescope/0"
    mode: Mode = Mode.Stand
    model: str = "Fake Domes Inc."
    style: Style = Style.Classic
    park_position: float = 155.0
    park_on_shutdown: bool = False
    close_on_shutdown: bool = False
    # dome position resolution in degrees
    az_resolution: float = 2
    slew_timeout: int = 120
    abort_timeout: int = 60
    init_timeout: int = 5
    open_timeout: int = 20
    close_timeout: int = 20
    # wind screen (DomeWindScreen domes only), all altitudes in degrees
    screen_timeout: int = 60
    # follow the telescope altitude when the dome is in Track mode
    screen_track: bool = True
    screen_offset: float = 0.0
    screen_min_alt: float = 0.0
    screen_max_alt: float = 90.0
    screen_park_position: float = 0.0
    # screen position resolution in degrees
    screen_alt_resolution: float = 2
    # list of fans of the dome, i.e.: fans: ['/FakeFan/fake1', '/FakeFan/fake2']
    fans: list[str] = field(default_factory=list[str])
    # list of lamps of the dome, i.e.: lamps: ['/FakeLamp/fake1']
    lamps: list[str] = field(default_factory=list[str])


class Dome(Interface):
    """
    A Roll-off or classic dome.
    """

    __config__: dict[str, Any] = {
        "device": None,
        "telescope": "/Telescope/0",
        "mode": Mode.Stand,
        "model": "Fake Domes Inc.",
        "style": Style.Classic,
        "park_position": 155.0,
        "park_on_shutdown": False,
        "close_on_shutdown": False,
        "az_resolution": 2,  # dome position resolution in degrees
        "slew_timeout": 120,
        "abort_timeout": 60,
        "init_timeout": 5,
        "open_timeout": 20,
        "close_timeout": 20,
        # wind screen (DomeWindScreen domes only), all altitudes in degrees
        "screen_timeout": 60,
        "screen_track": True,  # follow the telescope alt when in Track mode
        "screen_offset": 0.0,
        "screen_min_alt": 0.0,
        "screen_max_alt": 90.0,
        "screen_park_position": 0.0,
        "screen_alt_resolution": 2,  # screen position resolution in degrees
        "fans": [],  # list of fans of the dome, i.e.: fans: ['/FakeFan/fake1', '/FakeFan/fake2']
        "lamps": [],  # list of lamps of the dome, i.e.: lamps: ['/FakeLamp/fake1']
    }

    def stand(self) -> None:
        """
        Tells the Dome to stand and only move when asked to.

        @rtype: None
        """

    def track(self) -> None:
        """
        Tells the Dome to track the telescope azimuth. Dome will use
        the telescope given in 'telescope' config parameter.
        @rtype: None
        """

    def get_mode(self) -> Mode:
        """
        Get the current Dome mode, Stand or Track, currently.

        @return: Dome's current mode.
        @rtype: Mode
        """
        ...

    def get_az(self) -> float:
        """
        Get the current dome Azimuth (Az)

        @return: Dome's current Az (decimal degrees)
        @rtype: float
        """
        ...


class DomeSlew(Dome):
    """Basic Interface for rotating observatory Domes."""

    def slew_to_az(self, az: float) -> None:
        """
        Slew to the given Azimuth.

        @param az: Azimuth in degrees.
        @type az: float

        @raises InvalidDomePositionException: When the request Azimuth
        is unreachable.

        @rtype: None
        """

    def is_slewing(self) -> bool:
        """
        Ask if the dome is slewing right now.

        @return: True if the dome is slewing, False otherwise.
        @rtype: bool
        """
        ...

    def abort_slew(self) -> None:
        """
        Try to abort the current slew.

        @return: False if slew couldn't be aborted, True otherwise.
        @rtype: bool
        """

    @event
    def slew_begin(self, position: float) -> None:
        """
        Indicates that the a new slew operation started.

        @param position: The dome current position when the slew started
        @type  position: float
        """

    @event
    def slew_complete(self, position: float, status: DomeStatus) -> None:
        """
        Indicates that the last slew operation finished (with or
        without success, check L{status} field for more information.).

        @param position: The dome current position when the slew finished in
        decimal degrees.
        @type  position: float

        @param status: Status of the slew command
        @type  status: L{DomeStatus}
        """


class DomeSlit(Dome):
    """
    Dome with Slit
    """

    def open_slit(self) -> None:
        """
        Open the dome slit.

        @rtype: None
        """

    def close_slit(self) -> None:
        """
        Close the dome slit.

        @rtype: None
        """

    def is_slit_open(self) -> bool:
        """
        Ask the dome if the slit is opened.

        @return: True when open, False otherwise.
        @rtype: bool
        """
        ...

    @event
    def slit_opened(self, az: float) -> None:
        """
        Indicates that the slit was just opened

        @param az: The azimuth when the slit opend
        @type  az: float
        """

    @event
    def slit_closed(self, az: float) -> None:
        """
        Indicates that the slit was just closed.

        @param az: The azimuth when the slit closed.
        @type  az: float
        """


class DomeFlap(Dome):
    """
    Dome with Flap
    """

    def open_flap(self) -> None:
        """
        Open the dome flap.

        @rtype: None
        """

    def close_flap(self) -> None:
        """
        Close the dome flap.

        @rtype: None
        """

    def is_flap_open(self) -> bool:
        """
        Ask the dome if the flap is open.

        @return: True when open, False otherwise.
        @rtype: bool
        """
        ...

    @event
    def flap_opened(self, az: float) -> None:
        """
        Indicates that the flap was just opened

        @param az: The azimuth when the flap opend
        @type  az: float
        """

    @event
    def flap_closed(self, az: float) -> None:
        """
        Indicates that the flap was just closed.

        @param az: The azimuth when the flap closed.
        @type  az: float
        """


class DomeWindScreen(Dome):
    """
    Dome with a wind screen: a screen that shades the lower part of the slit and
    is positioned in altitude.

    Altitudes are in decimal degrees, horizon = 0 and zenith = 90, the same
    convention used by ASCOM's Dome.Altitude.

    When the dome is in L{Mode.Track} and the 'screen_track' config option is
    set, the screen follows the telescope altitude plus 'screen_offset',
    clamped to ['screen_min_alt', 'screen_max_alt'].
    """

    def move_screen(self, alt: float) -> None:
        """
        Move the wind screen to the given altitude.

        The request is accepted with the slit closed as well: the screen must be
        at the requested altitude by the time the slit opens.

        @param alt: Screen altitude in decimal degrees.
        @type  alt: float

        @raises InvalidDomePositionException: When the requested altitude is
        outside the screen travel limits.

        @rtype: None
        """

    def get_screen(self) -> float:
        """
        Get the current wind screen altitude.

        @return: Screen current altitude in decimal degrees.
        @rtype: float
        """
        ...

    def is_screen_moving(self) -> bool:
        """
        Ask if the wind screen is moving right now.

        @return: True if the screen is moving, False otherwise.
        @rtype: bool
        """
        ...

    def abort_screen(self) -> None:
        """
        Try to abort the current screen movement.

        @rtype: None
        """

    @event
    def screen_begin(self, alt: float) -> None:
        """
        Indicates that a new screen movement started.

        @param alt: The screen altitude when the movement started, in decimal
        degrees.
        @type  alt: float
        """

    @event
    def screen_complete(self, alt: float, status: DomeStatus) -> None:
        """
        Indicates that the last screen movement finished (with or without
        success, check L{status} field for more information.).

        @param alt: The screen altitude when the movement finished, in decimal
        degrees.
        @type  alt: float

        @param status: Status of the screen command
        @type  status: L{DomeStatus}
        """


class DomeSync(Dome):
    """
    Synchronism operations with a chosen telescope.
    """

    @event
    def sync_begin(self) -> None:
        """
        Indicates that the dome was asked and is starting to sync with the telescope (if any).
        """

    @event
    def sync_complete(self) -> None:
        """
        Indicates that the dome was asked and finished the sync with the telescope (if any).
        """

    def sync_with_tel(self) -> None:
        """
        If dome was in Track mode, sync dome position with current scope position.

        @rtype: None
        """

    def is_sync_with_tel(self) -> bool:
        """
        If dome was in Track mode, returns wether the dome slit is synchronized with telescope azimuth.

        @rtype: bool
        """
        ...
