# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.interfaces.focuser import (
    InvalidFocusPositionException,
    FocuserFeature,
    FocuserAxis,
)

from chimera.instruments.focuser import FocuserBase
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY
from chimera.core.lock import lock
from chimera.util.enum import Enum

import os


class Direction(Enum):
    IN = "IN"
    OUT = "OUT"


__all__ = ["Direction", "DCFocuser"]


class DCFocuser(FocuserBase):
    """
    DCFocuser uses as standard DC pulse Focuser with a software
    layer to mimic the behaviour of a Encoder-based Focuser.

    You have to define two parameter:
     - 'dt': define the longest pulse possible to go end-to-end through the focuser.
     - 'pulse_dt': how long would a single unit pulse be.

    NOTE: For APIs which doesn't provide access to time driven focuser
    movements, dt and pulse_dt could be in whatever unit you like, for
    example: dt could be how in units of 'small pulse'. See
    TheSkyTelescope implementation of this class for an example.

    Those two paremeters will define the 'encoded' range of DCFocuser,
    for example: If dt=2000 ms and pulse_dt = 10 ms, this virtual
    encoded focuser would be 2000/10= 200 units (get_range would return
    (0, 200).

    Normally, before use this class you should do a handwork with a
    chronometer and pulse your focuser to one end and then time how
    long it takes to go end-to-en, unless your focuser manufacturer
    give this number for you.
    """

    __config__ = {
        "dt": 1000,  # how many milliseconds/pulses should I
        # use to traverse the whole focus range
        # (end-to-end).
        "pulse_dt": 10,
    }  # unit pulse length (ms)

    def __init__(self):
        FocuserBase.__init__(self)

        self._supports = {
            FocuserFeature.TEMPERATURE_COMPENSATION: False,
            FocuserFeature.POSITION_FEEDBACK: True,
            FocuserFeature.ENCODER: False,
            FocuserFeature.CONTROLLABLE_X: False,
            FocuserFeature.CONTROLLABLE_Y: False,
            FocuserFeature.CONTROLLABLE_Z: True,
            FocuserFeature.CONTROLLABLE_U: False,
            FocuserFeature.CONTROLLABLE_V: False,
            FocuserFeature.CONTROLLABLE_W: False,
        }

        self._position = 0
        self._range = None
        self._last_time_log = None

    def __start__(self):

        # range setting
        self._range = (0, int(self["dt"] / float(self["pulse_dt"])))
        if self._range[1] <= 0:
            self.log.warning(
                "Invalid dt and pulse_dt constants, focuser range negative."
            )
            return False

        # restore last position
        last_position = None

        filename = os.path.join(SYSTEM_CONFIG_DIRECTORY, "dc_focuser.memory")
        if os.path.exists(filename):
            try:
                last_position = int(open(filename, "r").read())
            except ValueError:
                self.log.warning(
                    "Content of dc_focuser.memory file is invalid. Removing it."
                )
                os.unlink(filename)

        self._last_position_log = open(filename, "w")

        # assume focuser is at the same position last time unless it was zero
        if last_position is None:
            self._position = self.get_range()[1]
        else:
            self._position = last_position

        # move focuser to our "zero" if needed
        if last_position is None:
            self.log.info("Focuser not calibrated. Wait ...")
            self.move_to(0)
            self.log.info("Calibration DONE")

        return True

    def _save_position(self, position):
        self._last_position_log.truncate()
        self._last_position_log.write(str(position))
        self._last_position_log.flush()

    @lock
    def move_in(self, n, axis=FocuserAxis.Z):
        self._check_axis(axis)
        return self._move(Direction.IN, n)

    @lock
    def move_out(self, n, axis=FocuserAxis.Z):
        self._check_axis(axis)
        return self._move(Direction.OUT, n)

    @lock
    def move_to(self, position, axis=FocuserAxis.Z):
        self._check_axis(axis)

        current = self.get_position()

        delta = position - current

        try:
            if delta > 0:
                self._move(Direction.OUT, abs(delta))
            elif delta < 0:
                self._move(Direction.IN, abs(delta))
        except (InvalidFocusPositionException, ValueError):
            self.log.error(f"Invalid position {position}.")
            return

        self._save_position(position)
        self._position = position

        return True

    def _move(self, direction, steps):

        if not self._in_range(direction, steps):
            raise InvalidFocusPositionException(f"{steps} is outside focuser limits.")

        if direction not in Direction:
            raise ValueError(f"Invalid direction '{direction}'.")

        self._move_to(direction, steps)

        return True

    def _in_range(self, direction, n):

        # Assumes:
        #   0 -------  N
        #  IN         OUT

        current = self.get_position()

        if direction == Direction.IN:
            target = current - n
        else:
            target = current + n

        min_pos, max_pos = self.get_range()

        return min_pos <= target <= max_pos

    def get_position(self, axis=FocuserAxis.Z):
        self._check_axis(axis)
        return self._position

    def get_range(self, axis=FocuserAxis.Z):
        self._check_axis(axis)
        return self._range
