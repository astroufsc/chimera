# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class GuiderStatus(Enum):
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
    __config__ = {
        "site": "/Site/0",  # Telescope Site.
        "telescope": "/Telescope/0",  # Telescope instrument that will be guided by the autoguider.
        "camera": "/Camera/0",  # Guider camera instrument.
        "max_acquire_tries": 3,  # Number of tries to find a guiding star.
        "max_fit_tries": 3,  # Number of tries to acquire the guide star offset before being lost.
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

        @param wait: Block until the guider has settled (or failed) instead
                     of returning right after the sequence is started.
        @type wait: bool

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

        @rtype: bool
        """
        raise NotImplementedError()

    def get_status(self):
        """Returns the current guider status.

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
        @type ra_only: bool

        @param wait: Block until the guider has settled at the new position.
        @type wait: bool

        Raises:
            GuiderException: If not guiding or the dither failed.
        """
        raise NotImplementedError()

    def find_star(self):
        """Attempts to find a guide star in the current field of view.

        Returns the (x, y) position of the selected guide star.

        Raises:
            StarNotFoundException: If no star is found.
        """

        raise NotImplementedError()

    @event
    def offset_complete(self, offset):
        """Raised after every offset is complete."""

    @event
    def guide_start(self, position):
        """Raised when a guider sequence starts."""

    @event
    def guide_stop(self, state, msg=None):
        """Raised when a guider sequence stops."""

    @event
    def star_acquired(self, position):
        """Raised when the guide star is acquired."""

    @event
    def star_lost(self):
        """Raised when the guide star is lost."""

    @event
    def dither_complete(self, offset, status):
        """Raised when a dither offset finishes settling."""
