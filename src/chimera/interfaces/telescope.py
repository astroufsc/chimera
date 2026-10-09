# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
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
    """Which side a German equatorial is on -- in **two different senses**.

    `EAST`/`WEST` is ASCOM's `SideOfPier`: a **mechanical** fact about the
    tube, and what a mount reports. `NORMAL`/`BEYOND` is Wallace's pointing
    state (SPIE 7019 §3.5): a **geometric** configuration of the pointing
    model, defined by `|mechanical declination| > 90°`.

    **They are two quantities wearing one word, and they do not always agree.**
    The ASCOM note that exists to disentangle them -- Simpson 2009, with
    Wallace in its acknowledgements -- shows them disagreeing at the same four
    sky positions. Which of a given mount's mechanical sides is "normal" is a
    property of *that mount*, so the mapping belongs to each driver and not to
    this enum: an AM5's `:Gm#` answers `E`/`W` and says nothing about which one
    a pointing model should call normal.

    Read the mechanical value with `get_pier_side` and the geometric one with
    `get_mount_side`. A driver that cannot tell returns `UNKNOWN` from either.

    **Compare with `==`, never `is`, and never touch `.value`.** This is a
    `StrEnum` and chimera's bus serialises with msgspec and no `dec_hook`, so a
    member that crosses a bus arrives as a plain `str`: `is` fails and `.value`
    raises. Same-bus calls pass the object by reference, which is the only
    reason existing `is` assertions pass.

    `NORMAL`/`BEYOND` were appended in 2026-08 and the three original members
    kept their names and values, so anything reading `EAST`/`WEST` is
    unaffected. They are appended rather than inserted because the WS codegen
    emits members in declaration order.
    """

    EAST = "EAST"
    WEST = "WEST"
    UNKNOWN = "UNKNOWN"
    NORMAL = "NORMAL"
    BEYOND = "BEYOND"


class PositionOutsideLimitsException(ChimeraException):
    pass


class Telescope(Interface):
    """
    Telescope base interface.
    """

    __config__ = {
        "device": None,
        "model": "Fake Telescopes Inc.",
        # free-form OPTICS header text (Newtonian, SCT, RCT, CDK, ...)
        "optics": "Newtonian",
        "mount": "Mount type Inc.",
        "aperture": 100.0,  # mm
        "focal_length": 1000.0,  # mm
        "focal_reduction": 1.0,  # ex., 0.5 for a half length focal reducer
        "fans": [],  # List of fans of the telescope, i.e.: ['/FakeFan/fake1', '/FakeFan/fake2']
    }


class TelescopeSlew(Telescope):
    """
    Basic interface for telescopes.
    """

    __config__ = {
        "timeout": 30,  # s
        "slew_rate": None,  # Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        "auto_align": True,
        "align_mode": AlignMode.POLAR,
        "slew_idle_time": 0.1,  # s
        "max_slew_time": 90.0,  # s
        "stabilization_time": 2.0,  # s
        "position_sigma_delta": 60.0,  # arcseconds
        "skip_init": False,
        "min_altitude": 20,
        # Hour angle, in hours, at which a German equatorial mount that tracked
        # into it is flipped to the other side of the pier. None (the default)
        # never flips.
        "pier_flip_ha": None,
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
        ...

    def slew_to_ra_dec(self, ra: float, dec: float, epoch: float = 2000) -> None:
        """
        Slew the scope to the given equatorial coordinates. Coordinates are always in ICRS frame.

        @param ra: Right Ascension to slew to in hours.
        @type ra: float

        @param dec: Declination to slew to in degrees.
        @type dec: float

        @param epoch: Epoch for the coordinates, default is 2000.
        @type epoch: float

        @returns: Nothing.
        @rtype: None
        """
        ...

    def slew_to_alt_az(self, alt: float, az: float) -> None:
        """
        Slew the scope to the given local coordinates.

        @param alt: Altitude to slew to in degrees.
        @type alt: float

        @param az: Azimuth to slew to in degrees.
        @type az: float

        @returns: Nothing.
        @rtype: None
        """
        ...

    def abort_slew(self) -> None:
        """
        Try to abort the current slew.

        @return: Nothing.
        @rtype: None
        """
        ...

    def is_slewing(self) -> bool:
        """
        Ask if the telescope is slewing right now.

        @return: True if the telescope is slewing, False otherwise.
        @rtype: bool
        """
        ...

    def move_east(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds East (if offset positive, West
        otherwise)

        @param offset: Arcseconds to move East.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """
        ...

    def move_west(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds West (if offset positive, East
        otherwise)

        @param offset: Arcseconds to move West.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """
        ...

    def move_north(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds North (if offset positive, South
        otherwise)

        @param offset: Arcseconds to move North.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """
        ...

    def move_south(self, offset: float, rate: float | None = None) -> None:
        """
        Move the scope I{offset} arcseconds South (if offset positive, North
        otherwise)

        @param offset: Arcseconds to move South.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """
        ...

    def move_offset(
        self, offset_ra: float, offset_dec: float, rate: float | None
    ) -> None:
        """
        @param offset_ra: Arcseconds to move in RA.
        @type  offset_ra: int or float

        @param offset_dec: Arcseconds to move in Dec
        @type  offset_dec: int or float

        @param rate: Slew rate to be used when moving in Degrees per second. If None, use the default rate.
        @type  rate: float | None

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """
        ...

    def get_ra(self) -> float:
        """
        Get the current telescope Right Ascension in hours.

        @return: Telescope's current Right Ascension in hours. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: float
        """
        ...

    def get_dec(self) -> float:
        """
        Get the current telescope Declination in degrees.

        @return: Telescope's current Declination in degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: float
        """
        ...

    def get_az(self) -> float:
        """
        Get the current telescope Azimuth.

        @return: Telescope's current Azimuth in degrees.
        @rtype: float
        """
        ...

    def get_alt(self) -> float:
        """
        Get the current telescope Altitude in degrees.

        @return: Telescope's current Altitude in degrees.
        @rtype: float
        """
        ...

    def get_position_ra_dec(self) -> tuple[float, float]:
        """
        Get the current position of the telescope in equatorial coordinates.

        @return: Telescope's current position (ra, dec) in hours and degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: Tuple[float, float]
        """
        ...

    def get_position_alt_az(self) -> tuple[float, float]:
        """
        Get the current position of the telescope in local coordinates.

        @return: Telescope's current position (alt, az) in degrees. ICRS coordinates and current, i.e. NOW, epoch.
        @rtype: Tuple[float, float]
        """
        ...

    def get_target_ra_dec(self) -> tuple[float, float, float]:
        """
        Get the current telescope target in equatorial coordinates.

        @return: Telescope's current target (ra, dec, epoch) in hours, degrees and epoch in years.
        @rtype: Tuple[float, float, float]
        """
        ...

    def get_target_alt_az(self) -> tuple[float, float]:
        """
        Get the current telescope target in local coordinates.

        @return: Telescope's current target (alt, az) in degrees.
        @rtype: Tuple[float, float]
        """
        ...

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
        ...

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
        ...


class TelescopePier(Telescope):
    def get_pier_side(self) -> TelescopePierSide:
        """
        Get the current MECHANICAL side of pier -- ASCOM's SideOfPier.

        This is what the mount reports about its own tube. For the geometric
        pointing state a model needs, use L{get_mount_side}; the two are
        different quantities and a mount decides how they relate.

        @return: Telescope current pier side: UNKNOWN, EAST or WEST.
        @rtype: L{TelescopePierSide}
        """
        ...

    def set_pier_side(self, side: TelescopePierSide) -> None:
        """
        Sets side of pier of the telescope.

        @param side: Side of pier: EAST or WEST
        @type  side: L{TelescopePierSide}

        @return: Nothing.
        @rtype: None
        """
        ...

    def get_mount_side(self) -> TelescopePierSide:
        """
        Get the current GEOMETRIC pointing state -- Wallace's normal/beyond.

        This is the quantity a pointing model means: BEYOND is the
        beyond-the-pole configuration, |mechanical declination| > 90 degrees,
        in which Wallace SPIE 7019 Eqn 24 reverses the sign of the collimation
        and non-perpendicularity terms. NORMAL is the other one.

        Each driver derives it from its own axes, because which mechanical side
        is "normal" is a property of the mount rather than of this interface. A
        driver that cannot tell returns UNKNOWN, and callers must treat that as
        "do not fit a pier-side-dependent term", not as NORMAL.

        @return: Telescope current pointing state: UNKNOWN, NORMAL or BEYOND.
        @rtype: L{TelescopePierSide}
        """
        ...


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
        ...

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
        ...

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
        ...


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
        ...

    def unpark(self) -> None:
        """
        Wake up the telescope of the last park operation.

        @return: Nothing.
        @rtype: None
        """
        ...

    def is_parked(self) -> bool:
        """
        Ask if the telescope is at park position.

        @return: True if the telescope is parked, False otherwise.
        @rtype: bool
        """
        ...

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
        ...

    def get_park_position(self) -> tuple[float, float]:
        """
        Get the Current park position.

        @return: Current park position (alt, az) in degrees.
        @rtype: Tuple[float, float]
        """
        ...

    @event
    def park_complete(self) -> None:
        """
        Indicates that the scope has parked successfully.
        """
        ...

    @event
    def unpark_complete(self) -> None:
        """
        Indicates that the scope has unparked (waked up)
        successfully.
        """
        ...


class TelescopeCover(Telescope):
    """
    Telescope with mirror cover.
    """

    def open_cover(self) -> None:
        """
        Open the telescope cover

        @return: None
        """
        ...

    def close_cover(self) -> None:
        """
        Close the telescope cover

        @return: None
        """
        ...

    def is_cover_open(self) -> bool:
        """
        Ask if the telescope cover is open or not

        @return: True if cover is open, false otherwise
        """
        ...


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
        ...

    def stop_tracking(self) -> None:
        """
        Stop telescope tracking.

        @return: Nothing.
        @rtype: None
        """
        ...

    def is_tracking(self) -> bool:
        """
        Ask if the telescope is tracking.

        @return: True if the telescope is tracking, False otherwise.
        @rtype: bool
        """
        ...

    @event
    def tracking_started(self) -> None:
        """
        Indicates that a tracking operation started.
        """
        ...

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
        ...


class TelescopeAxis(Telescope):
    """
    A telescope whose mechanical axis positions can be read directly.

    Sky coordinates are what a mount reports; axis positions are what it
    actually did. A pointing model is fitted between the two, so a client
    building one needs the second — unfiltered by whatever transform the
    mount applies on the way out, and at the resolution the mechanism has
    rather than the resolution its coordinate replies happen to have.

    Axes are named after Wallace's generic pair (TCSpk): roll and pitch are
    [-h, dec] on an equatorial and [pi - az, alt] on an altazimuth. Naming
    them that way keeps either mount type from being built into the
    interface, which is the same reason TCSpk does it.
    """

    def get_axis_counts(self) -> tuple[int, int]:
        """Current mechanical position of both axes, in controller counts.

        Counts are the mount's own integer unit, reported exactly: no
        rounding, no epoch, no site, no coordinate transform. The zero point
        is arbitrary and may move across power cycles — a client fitting a
        pointing model absorbs it into its index terms rather than asking
        the mount to be honest about it.

        Returns (roll, pitch) counts.

        Raises:
            NotImplementedError: If the mount cannot report axis position.
        """
        raise NotImplementedError()

    def get_axis_scale(self) -> tuple[float, float]:
        """Arcseconds of axis rotation per count, as (roll, pitch).

        Constant for a given mount. Counts per revolution, if a caller wants
        it, is 1296000 divided by this.
        """
        raise NotImplementedError()


class TelescopeAxisRate(Telescope):
    """
    A telescope accepting a continuous rate on each mechanical axis.

    The rate is an *addition* to whatever the mount is already doing: a
    tracking mount given a rate tracks and offsets at once. This is the
    actuator a closed correction loop drives, and it is a different thing
    from the timed open-loop nudges of L{TelescopeSlew.move_east} and its
    siblings, which are offsets rather than rates.

    Units follow ASCOM's RightAscensionRate/DeclinationRate pair, which is
    the same concept: arcseconds per second, zero meaning plain tracking.
    Note that ASCOM's MoveAxis is a different thing again, in deg/s.
    """

    def set_axis_rate(self, roll: float, pitch: float) -> None:
        """Set a continuous rate on each axis, in arcseconds per second.

        Zero on both axes returns the mount to plain tracking. Resolution
        and maximum are device specific, and a driver clamps rather than
        raising, so a control loop should read back with L{get_axis_rate}
        rather than assume the rate it asked for is the rate it got.

        @param roll: Rate on the roll axis, arcsec/s.
        @param pitch: Rate on the pitch axis, arcsec/s.

        Raises:
            NotImplementedError: If the mount cannot accept axis rates.
        """
        raise NotImplementedError()

    def get_axis_rate(self) -> tuple[float, float]:
        """The rates currently in effect, as (roll, pitch) in arcsec/s.

        What the mount is actually doing, after any clamping or
        quantisation it applied to the last L{set_axis_rate}.
        """
        raise NotImplementedError()


class TelescopePointingModel(Telescope):
    """
    A telescope carrying its own internal pointing model.

    Most mounts keep a table of sync points, interpolate over it, and warp
    the sky-to-axis map underneath the client. A client fitting its own
    model needs that switched off, and needs to be able to prove it is off:
    otherwise it is fitting the residuals of someone else's model, and every
    statistical judgment it makes about its own is quietly wrong.

    Distinct from L{AlignMode}, which is mount geometry — ASCOM calls that
    AlignmentMode — and says nothing about a model.
    """

    def clear_pointing_model(self) -> None:
        """Discard every alignment point, leaving the model null.

        Raises:
            NotImplementedError: If the mount has no model to clear.
        """
        raise NotImplementedError()

    def apply_pointing_model(self, ra: float, dec: float) -> tuple[float, float]:
        """Run one coordinate pair through the mount's model, without moving.

        A side-effect-free oracle. Sweep a grid through it and compare
        against the input: an identity result means the model really is
        null, which is the only way to check that L{clear_pointing_model}
        did what it said.

        @param ra: Right ascension, hours.
        @param dec: Declination, degrees.

        Returns the transformed (ra, dec), in the same units.

        Raises:
            NotImplementedError: If the mount cannot evaluate its model
                without slewing.
        """
        raise NotImplementedError()
