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
from random import Random
import threading

from chimera.core.chimeraobject       import ChimeraObject

from chimera.interfaces.dome        import InvalidDomePositionException
from chimera.interfaces.domedriver  import IDomeDriver

from chimera.core.lock import lock


class FakeDome (ChimeraObject, IDomeDriver):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self._position  = 0
        self._slewing = False
        self._slitOpen  = False
        self._abort = threading.Event()

    @lock
    def slewToAz (self, az):

        if az > 360:
            raise InvalidDomePositionException("Cannot slew to %s. "
                                               "Outise azimute limits." % az)

        self._abort.clear()
        self._slewing = True
        
        self.slewBegin(az)

        slew_time = (Random().random()*self["slew_timeout"]) / 10

        t=0
        while t < slew_time:
            if self._abort.isSet():
                self._slewing = False
                return

            time.sleep (0.1)            
            t+=0.1

        self._position = az # move :)

        self._slewing = False

        self.slewComplete(self.getAz())

    def isSlewing (self):
        return self._slewing

    def abortSlew (self):
        if not self.isSlewing(): return

        self._abort.set()

        while self.isSlewing(): time.sleep(0.1)
            
        self.abortComplete(self.getAz())

    @lock
    def openSlit (self):
        self._slitOpen = True

    @lock
    def closeSlit (self):
        self._slitOpen = False

    def isSlitOpen (self):
        return self._slitOpen

    @lock
    def getAz(self):
        return self._position
