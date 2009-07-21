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

from chimera.core.lock          import lock

from chimera.interfaces.focuser import (FocuserFeature,
                                        InvalidFocusPositionException)

from chimera.instruments.focuser import FocuserBase


class FakeFocuser (FocuserBase):

    def __init__ (self):
        FocuserBase.__init__(self)

        self._position = 0

        self._supports = {FocuserFeature.TEMPERATURE_COMPENSATION: False,
                          FocuserFeature.POSITION_FEEDBACK: True,
                          FocuserFeature.ENCODER: True}

    def __start__ (self):
        self._position = int(self.getRange()[1] / 2.0)
        self["model"] = "Fake Focus v.1"

    @lock
    def moveIn (self, n):
        target = self.getPosition() - n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % target)
    @lock
    def moveOut (self, n):
        target = self.getPosition() + n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % target)
    @lock
    def moveTo (self, position):
        if self._inRange(position):
            self._setPosition(position)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % int(position))
    @lock
    def getPosition (self):
        return self._position

    def getRange (self):
        return (0, 7000)

    def _setPosition (self, n):
        self.log.info("Changing focuser to %s" % n)
        self._position = n

    def _inRange (self, n):
        min_pos, max_pos = self.getRange()
        return (min_pos <= n <= max_pos)
