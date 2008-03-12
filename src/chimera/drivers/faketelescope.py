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

from chimera.interfaces.telescopedriver import ITelescopeDriverSlew
from chimera.interfaces.telescopedriver import ITelescopeDriverSync
from chimera.interfaces.telescopedriver import ITelescopeDriverPark
from chimera.interfaces.telescopedriver import SlewRate

from chimera.core.chimeraobject         import ChimeraObject

from chimera.core.lock import lock


class FakeTelescope (ChimeraObject,
                     ITelescopeDriverSlew,
                     ITelescopeDriverSync,
                     ITelescopeDriverPark):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self.__slewing = False

    def __start__ (self):
        self.setHz(1.0/10)

    def open(self):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    @lock
    def slewToRaDec(self, position):
        self.slewBegin(position)
        time.sleep(2)
        self.slewComplete(position)

    @lock
    def slewToAltAz(self, position):
        pass

    def isSlewing (self):
        pass

    @lock
    def abortSlew(self):
        pass

    @lock
    def moveEast(self, offset, rate=SlewRate.MAX):
        pass

    @lock
    def moveWest(self, offset, rate=SlewRate.MAX):
        pass

    @lock
    def moveNorth(self, offset, rate=SlewRate.MAX):
        pass

    @lock
    def moveSouth(self, offset, rate=SlewRate.MAX):
        pass

    def getRa(self):
        pass

    def getDec(self):
        pass

    def getAz(self):
        pass

    def getAlt(self):
        pass

    def getPositionRaDec(self):
        pass

    def getPositionAzAlt(self):
        pass

    def getTargetRaDec(self):
        pass

    def getTargetAzAlt(self):
        pass 

    def sync(self, position):
        pass

    def park(self):
        pass

    def unpark(self):
        pass

    def isParked(self):
        pass

    def setParkPosition (self, position):
        pass
