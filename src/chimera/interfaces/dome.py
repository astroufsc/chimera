# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from dataclasses import dataclass, field
from typing import Any

from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum

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
    Dome with Slit
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
