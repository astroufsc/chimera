# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from typing import Tuple
from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.util.enum import Enum


class AlignMode(Enum):
    ALT_AZ = "ALT_AZ"
    POLAR = "POLAR"
    LAND = "LAND"


class TelescopeStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    ABORTED = "ABORTED"
    OBJECT_TOO_LOW = "OBJECT_TOO_LOW"
    OBJECT_TOO_HIGH = "OBJECT_TOO_HIGH"


class TelescopePierSide(Enum):
    EAST = "EAST"
    WEST = "WEST"
    UNKNOWN = "UNKNOWN"


class PositionOutsideLimitsException(ChimeraException):
    pass


class Telescope(Interface):
    """
    Telescope base interface.
    """

    __config__ = {
        "device": None,
        "model": "Fake Telescopes Inc.",
        "optics": ["Newtonian", "SCT", "RCT"],
        "mount": "Mount type Inc.",
        "aperture": 100.0,  # mm
        "focal_length": 1000.0,  # mm unit (ex., 0.5 for a half length focal reducer)
        "focal_reduction": 1.0,
        "fans": [],  # List of fans of the telescope, i.e.: ['/FakeFan/fake1', '/FakeFan/fake2']
    }


class TelescopeSlew(Telescope):
    """
    Basic interface for telescopes.
    """

    __config__ = {
        "timeout": 30,  # s
        "slew_rate": None,  # Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        "auto_align": True,
        "align_mode": AlignMode.POLAR,
        "slew_idle_time": 0.1,  # s
        "max_slew_time": 90.0,  # s
        "stabilization_time": 2.0,  # s
        "position_sigma_delta": 60.0,  # arcseconds
        "skip_init": False,
        "min_altitude": 20,
    }

    def slew_to_object(self, name: str) -> None:
        """
        Slew the scope to the coordinates of the given
        object. Object name will be converted to a coordinate using a
        resolver like SIMBAD or NED.

        @param name: Object name to slew to.
        @type  name: str

        @returns: Nothing.
        @rtype: None
        """

    def slew_to_ra_dec(self, ra: float, dec: float, epoch: float = 2000) -> None:
        """
        Slew the scope to the given equatorial coordinates.

        @param ra: Right Ascension to slew to.
        @type ra: float

        @param dec: Declination to slew to.
        @type dec: float

        @param epoch: Epoch for the coordinates, default is 2000.
        @type epoch: float

        @returns: Nothing.
        @rtype: None
        """

    def slew_to_alt_az(self, alt: float, az: float) -> None:
        """
        Slew the scope to the given local coordinates.

        @param alt: Altitude to slew to.
        @type alt: float

        @param az: Azimuth to slew to.
        @type az: float

        @returns: Nothing.
        @rtype: None
        """

    def abort_slew(self) -> None:
        """
        Try to abort the current slew.

        @return: Nothing.
        @rtype: None
        """

    def is_slewing(self) -> bool:
        """
        Ask if the telescope is slewing right now.

        @return: True if the telescope is slewing, False otherwise.
        @rtype: bool
        """

    def move_east(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds East (if offset positive, West
        otherwise)

        @param offset: Arcseconds to move East.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def move_west(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds West (if offset positive, East
        otherwise)

        @param offset: Arcseconds to move West.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def move_north(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds North (if offset positive, South
        otherwise)

        @param offset: Arcseconds to move North.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def move_south(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds South (if offset positive, North
        otherwise)

        @param offset: Arcseconds to move South.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def move_offset(
        self, offset_ra: float, offset_dec: float, rate: float | None
    ) -> None:
        """
        @param offset_ra: Arcseconds to move in RA.
        @type  offset_ra: int or float

        @param offset_dec: Arcseconds to move in Dec
        @type  offset_dec: int or float

        @param rate: Slew rate to be used when moving in Arcseconds per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def get_ra(self) -> float:
        """
        Get the current telescope Right Ascension.

        @return: Telescope's current Right Ascension in hours. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: float
        """

    def get_dec(self) -> float:
        """
        Get the current telescope Declination.

        @return: Telescope's current Declination in degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: float
        """

    def get_az(self) -> float:
        """
        Get the current telescope Azimuth.

        @return: Telescope's current Azimuth in degrees.
        @rtype: float
        """

    def get_alt(self) -> float:
        """
        Get the current telescope Altitude.

        @return: Telescope's current Altitude in degrees.
        @rtype: float
        """

    def get_position_ra_dec(self) -> Tuple[float, float]:
        """
        Get the current position of the telescope in equatorial coordinates.

        @return: Telescope's current position (ra, dec) in hours and degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: Tuple[float, float]
        """

    def get_position_alt_az(self) -> Tuple[float, float]:
        """
        Get the current position of the telescope in local coordinates.

        @return: Telescope's current position (alt, az) in degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: Tuple[float, float]
        """

    def get_target_ra_dec(self) -> Tuple[float, float, float]:
        """
        Get the current telescope target in equatorial coordinates.

        @return: Telescope's current target (ra, dec, epoch) in hours, degrees and epoch in years.
        @rtype: Tuple[float, float, float]
        """

    def get_target_alt_az(self) -> Tuple[float, float]:
        """
        Get the current telescope target in local coordinates.

        @return: Telescope's current target (alt, az) in degrees.
        @rtype: Tuple[float, float]
        """

    @event
    def slew_begin(self, ra: float, dec: float, epoch: float) -> None:
        """
        Indicates that a slew operation started.

        @param ra: The Right Ascension where the telescope will slew to in hours.
        @type ra: float

        @param dec: The Declination where the telescope will slew to in degrees.
        @type dec: float

        @param epoch: The epoch of the coordinates, default is 2000.
        @type epoch: float

        @note: This event is fired when the slew starts, and coordinates are returned as they were received.
        """

    @event
    def slew_complete(self, ra: float, dec: float, status: TelescopeStatus) -> None:
        """
        Indicates that the last slew operation finished. This event
        will be fired even when problems impedes complete slew
        (altitude limits, for example). Check L{status} field if you
        need more information.

        @param ra: The Right Ascension where the telescope ended up in hours.
        @type  ra: float

        @param dec: The Declination where the telescope ended up in degrees.
        @type  dec: float

        @param status: The status of the slew operation.
        @type  status: L{TelescopeStatus}

        @note: This event is fired when the slew ends, and coordinates are returned as current, i.e. NOW, epoch.
        """


class TelescopePier(Telescope):
    def get_pier_side(self) -> TelescopePierSide:
        """
        Get the current side of pier of the telescope.

        @return: Telescope current pier side: UNKNOWN, EAST or WEST.
        @rtype: L{TelescopePierSide}
        """

    def set_pier_side(self, side: TelescopePierSide) -> None:
        """
        Sets side of pier of the telescope.

        @param side: Side of pier: EAST or WEST
        @type  side: L{TelescopePierSide}

        @return: Nothing.
        @rtype: None
        """


class TelescopeSync(Telescope):
    """
    Telescope with sync support.
    """

    def sync_object(self, name: str) -> None:
        """
        Synchronize the telescope using the coordinates of the
        given object.

        @param name: Object name to sync in.
        @type  name: str
        """

    def sync_ra_dec(self, ra: float, dec: float, epoch: float = 2000) -> None:
        """
        Synchronizes the telescope on the given equatorial
        coordinates.

        This mean different things to different telescopes, but the
        general idea is that after this command, the logical position
        that the telescope will return when asked about will be equal
        to the given position.

        @param ra: Right Ascension in hours.
        @type  ra: float

        @param dec: Declination in degrees.
        @type  dec: float

        @param epoch: The epoch of the coordinates, default is 2000.
        @type  epoch: float

        @return: Nothing
        @rtype: None
        """

    @event
    def sync_complete(self, ra: float, dec: float) -> None:
        """
        Fired when a synchronization operation finishes.

        @param ra: The Right Ascension where the telescope synced in hours.
        @type  ra: float

        @param dec: The Declination where the telescope synced in degrees.
        @type  dec: float

        @note: This event is fired when the sync ends, and coordinates are returned as current, i.e. NOW, epoch.
        """


class TelescopePark(Telescope):
    """
    Telescope with park/unpark support.
    """

    __config__ = {"default_park_position": (90, 180)}  # default park position alt, az

    def park(self) -> None:
        """
        Park the telescope on the actual saved park position
        (L{set_park_position}) or on the default position if none
        set.

        When parked, the telescope will not track objects and may be
        turned off (if the scope was able to).

        @return: Nothing.
        @rtype: None
        """

    def unpark(self) -> None:
        """
        Wake up the telescope of the last park operation.

        @return: Nothing.
        @rtype: None
        """

    def is_parked(self) -> bool:
        """
        Ask if the telescope is at park position.

        @return: True if the telescope is parked, False otherwise.
        @rtype: bool
        """

    def set_park_position(self, alt: float, az: float) -> None:
        """
        Defines where the scope will park when asked to.

        @param alt: Altitude coordinate to park the scope
        @type  alt: float

        @param az: Azimuth coordinate to park the scope
        @type  az: float

        @return: Nothing.
        @rtype: None
        """

    def get_park_position(self) -> Tuple[float, float]:
        """
        Get the Current park position.

        @return: Current park position (alt, az) in degrees.
        @rtype: Tuple[float, float]
        """

    @event
    def park_complete(self) -> None:
        """
        Indicates that the scope has parked successfully.
        """

    @event
    def unpark_complete(self) -> None:
        """
        Indicates that the scope has unparked (waked up)
        successfully.
        """


class TelescopeCover(Telescope):
    """
    Telescope with mirror cover.
    """

    def open_cover(self) -> None:
        """
        Open the telescope cover

        @return: None
        """

    def close_cover(self) -> None:
        """
        Close the telescope cover

        @return: None
        """

    def is_cover_open(self) -> bool:
        """
        Ask if the telescope cover is open or not

        @return: True if cover is open, false otherwise
        """


class TelescopeTracking(Telescope):
    """
    Telescope with support to start/stop tracking.
    """

    def start_tracking(self) -> None:
        """
        Start telescope tracking.

        @return: Nothing
        @rtype: None
        """

    def stop_tracking(self) -> None:
        """
        Stop telescope tracking.

        @return: Nothing.
        @rtype: None
        """

    def is_tracking(self) -> bool:
        """
        Ask if the telescope is tracking.

        @return: True if the telescope is tracking, False otherwise.
        @rtype: bool
        """

    @event
    def tracking_started(self) -> None:
        """
        Indicates that a tracking operation started.
        """

    @event
    def tracking_stopped(self, status: TelescopeStatus) -> None:
        """
        Indicates that the last tracking operation stopped. This event
        will be fired even when problems impedes tracking operation to resume
        (altitude limits, for example). Check L{status} field if you
        need more information.

        @param status: The status of the tracking operation.
        @type  status: L{TelescopeStatus}

        @return: None
        @rtype: None
        """
