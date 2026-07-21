# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class GuiderStatus(Enum):
    """Guider states.

    Every implementation must be able to report OFF, GUIDING and ERROR.
    The rest are optional: a backend that has no separate calibration step
    never reports CALIBRATING, and one with no settling notion never
    reports SETTLING. Clients must not treat their absence as an error.
    """

    OK = "OK"
    GUIDING = "GUIDING"
    CALIBRATING = "CALIBRATING"
    SETTLING = "SETTLING"
    PAUSED = "PAUSED"
    OFF = "OFF"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class StarNotFoundException(ChimeraException):
    pass


class GuiderException(ChimeraException):
    pass


class Autoguider(Interface):
    """A closed-loop guider driving corrections into the mount.

    Guiding is normally performed by an external package (TheSkyX, PHD2),
    which owns the guide camera and the mount connection itself. This
    interface therefore does not name chimera instruments: an
    implementation talks to its backend and reports what it is doing.

    Positions and dither amounts are in GUIDER DETECTOR PIXELS, not sky
    units, since that is the only frame every backend agrees on.
    """

    __config__ = {
        "exptime": None,  # Guide exposure (s). None keeps the backend's own setting.
        "recalibrate": False,  # Recalibrate on every start_guiding, not just when asked.
        "max_acquire_tries": 3,  # Number of tries to find a guiding star.
        "settle_pixels": 1.5,  # Maximum guide distance (pixels) to consider guiding settled/stable.
        "settle_time": 10.0,  # Minimum time (s) the guider must remain below settle_pixels.
        "settle_timeout": 60.0,  # Maximum time (s) to wait for the guider to settle.
        "dither_amount": 3.0,  # Default dither amount (pixels).
        "dither_ra_only": False,  # Dither only in right ascension.
    }

    def start_guiding(self, recalibrate=False, wait=False):
        """Start a guiding sequence: acquire a guide star, calibrate if
        needed and begin sending corrections to the telescope.

        @param recalibrate: Discard the current calibration and recalibrate
                            before guiding.
        @type recalibrate: bool

        @param wait: Block until guiding is established instead of returning
                     right after the sequence is started. Backends with a
                     settling notion wait for settle_pixels/settle_time as
                     well; the others return once corrections have begun.
        @type wait: bool

        Returns the guide star position as [x, y] detector pixels, or None
        when the backend selected the star itself and does not report it.
        Callers that need the position should use the star_acquired event.

        Raises:
            StarNotFoundException: If no guide star could be acquired.
            GuiderException: If the guider could not be started.
        """
        raise NotImplementedError()

    def stop_guiding(self):
        """Stop the current guiding sequence.

        Raises:
            GuiderException: If the guider could not be stopped.
        """
        raise NotImplementedError()

    def abort(self):
        """Abort the current guiding sequence as soon as possible."""
        raise NotImplementedError()

    def is_guiding(self):
        """Returns True if a guiding sequence is currently active.

        A backend that keeps the loop running while the star is lost
        reports True here and GuiderStatus.ERROR from get_status(), so the
        two can disagree. Use this to decide whether to stop, and
        get_status() to decide whether guiding is healthy.

        @rtype: bool
        """
        raise NotImplementedError()

    def get_status(self):
        """Returns the current guider status.

        Must not raise: an unreachable backend reports GuiderStatus.ERROR.

        @rtype: GuiderStatus
        """
        raise NotImplementedError()

    def dither(self, amount=None, ra_only=None, wait=False):
        """Offset the guide star lock position by a small random amount
        and resume guiding at the new position.

        @param amount: Maximum dither offset (pixels). Uses the
                       'dither_amount' configuration value if None.
        @type amount: float

        @param ra_only: Dither only in right ascension. Uses the
                        'dither_ra_only' configuration value if None.
                        Backends that do not know the guider's sky
                        orientation dither along detector x instead, which
                        is RA only if the guider is aligned.
        @type ra_only: bool

        @param wait: Block until the guider has settled at the new position.
                     Ignored by backends with no settling notion.
        @type wait: bool

        Raises:
            GuiderException: If not guiding or the dither failed.
        """
        raise NotImplementedError()

    def find_star(self):
        """Attempts to find a guide star in the current field of view.

        Returns the selected guide star as [x, y] detector pixels.

        Whether this raises star_acquired depends on when the backend
        commits to the star: implementations that choose it themselves
        raise the event here, those that let the backend choose raise it
        later, once the backend reports its selection.

        Raises:
            StarNotFoundException: If no star is found.
        """

        raise NotImplementedError()

    @event
    def offset_complete(self, offset):
        """Raised after every guide correction.

        @param offset: A dict with the keys 'frame' (int), 'dx', 'dy'
                       (detector pixels), 'ra_distance', 'dec_distance'
                       (arcsec) and 'snr'. Any key may be missing when the
                       backend does not report it; consumers must default.

        Only backends that publish per-correction telemetry raise this.
        """

    @event
    def guide_start(self, position):
        """Raised when a guider sequence starts.

        @param position: Guide star as [x, y] detector pixels, or None if
                         the backend has not reported its selection yet.
        """

    @event
    def guide_stop(self, state, msg=None):
        """Raised when a guider sequence stops, including when it stops
        outside chimera.

        @param state: GuiderStatus.OFF for a normal stop,
                      GuiderStatus.ABORTED for abort(), GuiderStatus.ERROR
                      when guiding failed.
        @param msg: Optional detail, e.g. why guiding stopped.
        """

    @event
    def star_acquired(self, position):
        """Raised when the guide star is acquired.

        @param position: Guide star as [x, y] detector pixels.
        """

    @event
    def star_lost(self):
        """Raised when the guide star is lost.

        Only backends that can distinguish a lost star from a stopped
        guider raise this; the rest report GuiderStatus.ERROR instead.
        """

    @event
    def dither_complete(self, offset, status):
        """Raised when a dither offset has been applied.

        @param offset: Applied offset as [dx, dy] detector pixels, or None
                       if the backend does not report what it used.
        @param status: GuiderStatus.OK, or ERROR if the dither failed.

        On backends with a settling notion this fires after settling; on
        the others it fires as soon as the offset is applied, so it does
        not by itself mean guiding is stable again.
        """
