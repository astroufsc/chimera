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


from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.util.enum import Enum


AlignMode = Enum("ALT_AZ", "POLAR", "LAND")
SlewRate  = Enum("GUIDE", "CENTER", "FIND", "MAX")


class ITelescopeDriver (Interface):

    __config__ = {"device"    : "/dev/ttyS0",
                  "align_mode": AlignMode.POLAR}
    
 
class ITelescopeDriverSlew (ITelescopeDriver):

    __config__ = {"timeout"             : 30, # s
                  "slew_rate"           : SlewRate.MAX,
                  "auto_align"          : True,
                  "slew_idle_time"      : 0.1, # s
                  "max_slew_time"       : 90.0, # s
                  "stabilization_time"  : 2.0, # s
                  "position_sigma_delta": 60.0, # arcseconds
                  "skip_init"           : True} 
    # methods

    def open(self):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    def slewToRaDec(self, position):
        pass

    def slewToAltAz(self, position):
        pass

    def isSlewing (self):
        pass

    def abortSlew(self):
        pass

    def calibrateMove (self):
        pass

    def moveEast(self, offset, rate=SlewRate.MAX):
        pass

    def moveWest(self, offset, rate=SlewRate.MAX):
        pass

    def moveNorth(self, offset, rate=SlewRate.MAX):
        pass

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

    # events
    
    @event
    def slewBegin (self, target):
        pass

    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass


class ITelescopeDriverSync(ITelescopeDriver):

    def syncObject (self, name):
        pass

    def syncRaDec (self, position):
        pass

    def syncAzAlt (self, position):
        pass

    @event
    def syncComplete(self, position):
        pass


class ITelescopeDriverPark (ITelescopeDriver):

    __config__ = {"park_position_alt": 90.0,
                  "park_position_az": 180.0}
        
    # methods
    def park(self):
        pass

    def unpark(self):
        pass

    def isParked(self):
        pass

    def setParkPosition (self, position):
        pass

    # events
    @event
    def parkComplete(self, position):
        pass

    @event
    def unparkComplete (self, position):
        pass


class ITelescopeDriverTracking (ITelescopeDriver):

    def startTracking (self):
        pass

    def stopTracking (self):
        pass

    def isTracking (self):
        pass
