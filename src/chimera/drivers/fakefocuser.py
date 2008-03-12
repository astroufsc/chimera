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

import time
import random

from chimera.core.chimeraobject       import ChimeraObject

from chimera.interfaces.focuser       import InvalidFocusPositionException
from chimera.interfaces.focuserdriver import IFocuserDriver

from chimera.core.lock import lock


class FakeFocuser (ChimeraObject, IFocuserDriver):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self._position = 0

    def __start__ (self):

        self._position = int(self["max_position"] / 2)
        
        self.setHz(1.0/10)

    @lock
    def moveIn (self, n):

        target = self.getPosition() - n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % target)

    @lock
    def moveOut (self, n):
        
        target = self.getPosition() + n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % target)


    @lock
    def moveTo (self, position):

        if self._inRange(position):
            self._setPosition(position)
        else:
            raise InvalidFocusPositionException("%d is outside focuser boundaries." % position)
        
        return False

    def getPosition (self):
        return self._position

    def _setPosition (self, n):
        self._position = n

    def _inRange (self, n):
        return (self["min_position"] <= n <= self["max_position"])
