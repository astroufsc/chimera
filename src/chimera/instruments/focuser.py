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

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock          import lock

from chimera.interfaces.focuser import Focuser


class FocuserBase (ChimeraObject, Focuser):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self._supports = {}

    @lock
    def moveIn (self, n):
        raise NotImplementedError()

    @lock
    def moveOut (self, n):
        raise NotImplementedError()

    @lock
    def moveTo (self, position):
        raise NotImplementedError()

    @lock
    def getPosition (self):
        raise NotImplementedError()

    def getRange (self):
        raise NotImplementedError()

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            self.log.info("Invalid feature: %s" % str(feature))
            return False

    def getMetadata(self, request):
        return [('FOCUSER', str(self['model']), 'Focuser Model'),
                ('FOCUS',  self.getPosition(),
                 'Focuser position used for this observation')]

    def _inRange (self, n):
        min_pos, max_pos = self.getRange()
        return (min_pos <= n <= max_pos)

