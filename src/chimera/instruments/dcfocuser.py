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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from chimera.interfaces.focuser import (InvalidFocusPositionException,
                                        FocuserFeature)

from chimera.instruments.focuser import FocuserBase
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY
from chimera.core.lock import lock
from chimera.util.enum import Enum

import os

Direction = Enum("IN", "OUT")


__all__ = ['Direction',
           'DCFocuser']


class DCFocuser (FocuserBase):
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
    encoded focuser would be 2000/10= 200 units (getRange would return
    (0, 200).

    Normally, before use this class you should do a handwork with a
    chronometer and pulse your focuser to one end and then time how
    long it takes to go end-to-en, unless your focuser manufacturer
    give this number for you.
    """

    __config__ = {"dt": 1000, # how many milliseconds/pulses should I
                              # use to traverse the whole focus range
                              # (end-to-end).
                  "pulse_dt": 10} # unit pulse length (ms)

    def __init__ (self):
        FocuserBase.__init__ (self)

        self._supports = {FocuserFeature.TEMPERATURE_COMPENSATION: False,
                          FocuserFeature.POSITION_FEEDBACK: True,
                          FocuserFeature.ENCODER: False}

        self._position = 0
        self._range = None
        self._lastTimeLog = None

    def __start__ (self):

        # range setting
        self._range = (0, int(self["dt"]/float(self["pulse_dt"])))
        if self._range[1] <= 0:
            self.log.warning("Invalid dt and pulse_dt constants, focuser range negative.")
            return False

        # restore last position
        lastPosition = None

        filename = os.path.join(SYSTEM_CONFIG_DIRECTORY, "dc_focuser.memory")
        if os.path.exists(filename):
            try:
                lastPosition = int(open(filename, 'r').read())
            except ValueError:
                self.log.warning("Content of dc_focuser.memory file is invalid. Removing it.")
                os.unlink(filename)

        self._lastPositionLog = open(filename, 'w')

        # assume focuser is at the same position last time unless it was zero
        if lastPosition is None:
            self._position = self.getRange()[1]
        else:
            self._position = lastPosition

        # move focuser to our "zero" if needed
        if lastPosition is None:
            self.moveTo(0)

        return True

    def _savePosition(self, position):
        self._lastPositionLog.truncate()
        self._lastPositionLog.write(str(position))
        self._lastPositionLog.flush()
        
    @lock
    def moveIn (self, n):
        return self._move (Direction.IN, n)

    @lock
    def moveOut (self, n):
        return self._move (Direction.OUT, n)

    @lock
    def moveTo (self, position):

        current = self.getPosition ()

        delta = position - current

        try:
            if delta > 0:
                self._move (Direction.OUT, abs(delta))
            elif delta < 0:
                self._move (Direction.IN, abs(delta))
        except:
            return

        self._savePosition(position)
        self._position = position
        
        return True

    def _move (self, direction, steps):

        if not self._inRange(direction, steps):
            raise InvalidFocusPositionException("%d is outside focuser limits." % steps)
        
        if direction not in Direction:
            raise ValueError("Invalid direction '%s'." % direction)

        self._moveTo(direction, steps)

        return True

    def _inRange (self, direction, n):

        # Assumes:
        #   0 -------  N
        #  IN         OUT

        current = self.getPosition()

        if direction == Direction.IN:
            target = current - n
        else:
            target = current + n

        min_pos, max_pos = self.getRange()
        
        return (min_pos <= target <= max_pos)

    def getPosition (self):
        return self._position

    def getRange (self):
        return self._range
        
