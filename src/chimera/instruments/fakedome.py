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

from chimera.core.lock import lock
from chimera.util.coord import Coord

from chimera.interfaces.dome import InvalidDomePositionException
from chimera.instruments.dome import DomeBase

import time
import threading


class FakeDome (DomeBase):

    def __init__ (self):
        DomeBase.__init__(self)

        self._position  = 0
        self._slewing = False
        self._slitOpen  = False
        self._abort = threading.Event()
        self._maxSlewTime = 5/180.0

    @lock
    def slewToAz (self, az):

        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if az > 360:
            raise InvalidDomePositionException("Cannot slew to %s. "
                                               "Outside azimuth limits." % az)

        self._abort.clear()
        self._slewing = True
        
        self.slewBegin(az)
        self.log.info("Slewing to %s" % az)
        
        # slew time ~ distance from current position
        distance = abs(float(az-self._position))
        if distance > 180:
            distance = 360-distance

        self.log.info("Slew distance %.3f deg" % distance)

        slew_time = distance*self._maxSlewTime

        self.log.info("Slew time ~ %.3f s" % slew_time)
        
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
    def getAz(self):
        return self._position

    @lock
    def openSlit (self):
        self.log.info("Opening slit")
        self._slitOpen = True

    @lock
    def closeSlit (self):
        self.log.info("Closing slit")
        self._slitOpen = False

    def isSlitOpen (self):
        return self._slitOpen
