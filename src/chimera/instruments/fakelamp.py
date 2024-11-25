#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

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
                "Intensity %.2f out of range. Must be between (%.2f:%.2f]."
                % (intensity, int_i, int_f)
            )

    @lock
    def getIntensity(self):
        return self._intensity

    def getRange(self):
        return self._irange
