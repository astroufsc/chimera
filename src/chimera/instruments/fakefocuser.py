# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import random
from chimera.core.lock import lock

from chimera.interfaces.focuser import (
    FocuserFeature,
    InvalidFocusPositionException,
    FocuserAxis,
)

from chimera.instruments.focuser import FocuserBase


class FakeFocuser(FocuserBase):

    def __init__(self):
        FocuserBase.__init__(self)

        self._position = 0

        self._supports = {
            FocuserFeature.TEMPERATURE_COMPENSATION: True,
            FocuserFeature.POSITION_FEEDBACK: True,
            FocuserFeature.ENCODER: True,
            FocuserFeature.CONTROLLABLE_X: False,
            FocuserFeature.CONTROLLABLE_Y: False,
            FocuserFeature.CONTROLLABLE_Z: True,
            FocuserFeature.CONTROLLABLE_U: False,
            FocuserFeature.CONTROLLABLE_V: False,
            FocuserFeature.CONTROLLABLE_W: False,
        }

    def __start__(self):
        self._position = int(self.getRange()[1] / 2.0)
        self["model"] = "Fake Focus v.1"

    @lock
    def moveIn(self, n, axis=FocuserAxis.Z):
        self._checkAxis(axis)
        target = self.getPosition() - n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException(
                f"{target} is outside focuser boundaries."
            )

    @lock
    def moveOut(self, n, axis=FocuserAxis.Z):
        self._checkAxis(axis)
        target = self.getPosition() + n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException(
                f"{target} is outside focuser boundaries."
            )

    @lock
    def moveTo(self, position, axis=FocuserAxis.Z):
        self._checkAxis(axis)
        if self._inRange(position):
            self._setPosition(position)
        else:
            raise InvalidFocusPositionException(
                f"{int(position)} is outside focuser boundaries."
            )

    @lock
    def getPosition(self, axis=FocuserAxis.Z):
        self._checkAxis(axis)
        return self._position

    def getRange(self, axis=FocuserAxis.Z):
        self._checkAxis(axis)
        return (0, 7000)

    def getTemperature(self):
        return random.randrange(10, 30)

    def _setPosition(self, n):
        self.log.info(f"Changing focuser to {n}")
        self._position = n

    def _inRange(self, n):
        min_pos, max_pos = self.getRange()
        return min_pos <= n <= max_pos
