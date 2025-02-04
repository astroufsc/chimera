# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.lock import lock
from chimera.interfaces.lamp import LampDimmer, IntensityOutOfRangeException
from chimera.instruments.lamp import LampBase
import time


class FakeLamp(LampBase, LampDimmer):
    def __init__(self):
        LampBase.__init__(self)

        self._isOn = False
        self._intensity = 0.0
        self._irange = (0.0, 100.0)

    @lock
    def switchOn(self):
        if not self.isSwitchedOn():
            time.sleep(1.0)
            self._isOn = True

        return True

    @lock
    def switchOff(self):
        if self.isSwitchedOn():
            time.sleep(1.0)
            self._isOn = False
        return True

    def isSwitchedOn(self):
        return self._isOn

    @lock
    def setIntensity(self, intensity):
        int_i, int_f = self.getRange()

        if int_i < intensity <= int_f:
            self._intensity = intensity
            return True
        else:
            raise IntensityOutOfRangeException(
                f"Intensity {intensity:.2f} out of range. Must be between ({int_i:.2f}:{int_f:.2f}]."
            )

    @lock
    def getIntensity(self):
        return self._intensity

    def getRange(self):
        return self._irange
