# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import time

from chimera.core.lock import lock
from chimera.instruments.lamp import LampBase
from chimera.interfaces.lamp import IntensityOutOfRangeException, LampDimmer


class FakeLamp(LampBase, LampDimmer):
    def __init__(self):
        LampBase.__init__(self)

        self._is_on = False
        self._intensity = 0.0
        self._intensity_range = (0.0, 100.0)

    @lock
    def switch_on(self):
        if not self.is_switched_on():
            time.sleep(1.0)
            self._is_on = True

        return True

    @lock
    def switch_off(self):
        if self.is_switched_on():
            time.sleep(1.0)
            self._is_on = False
        return True

    def is_switched_on(self):
        return self._is_on

    @lock
    def set_intensity(self, intensity):
        range_start, range_end = self.get_range()

        if range_start < intensity <= range_end:
            self._intensity = intensity
            return True
        else:
            raise IntensityOutOfRangeException(
                f"Intensity {intensity:.2f} out of range. Must be between ({range_start:.2f}:{range_end:.2f}]."
            )

    @lock
    def get_intensity(self):
        return self._intensity

    def get_range(self):
        return self._intensity_range
