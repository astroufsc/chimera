#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

class ITelescope (Interface):

    __options__ = {"driver": "/Fake/telescope"}
    

class ITelescopeSlew (ITelescope):

    # methods
    def slewToRaDec (self, ra, dec):
        pass

    def slewToAzAlt (self, az, alt):
        pass

    def isSlewing (self):
        pass

    def moveEast (self, offset):
        pass

    def moveWest (self, offset):
        pass

    def moveNorth (self, offset):
        pass

    def moveSouth (self, offset):
        pass

    def abortSlew (self):
        pass

    def getRa (self):
        pass
    
    def getDec (self):
        pass

    def getAz (self):
        pass

    def getAlt (self):
        pass

    def getPosition (self):
        pass

    def getTarget (self):
        pass

    # events

    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass

class ITelescopeSync(Interface):

    # methods
    def sync(self, coord):
        pass
    
    # events
    @event
    def syncComplete(self, position):
        pass

class ITelescopePark (Interface):
        
    # methods
    def park(self):
        pass

    def unpark(self):
        pass

    def setParkPosition (self, coord):
        pass

    # events
    @event
    def parkComplete(self, position):
        pass

    @event
    def unparkComplete (self):
        pass


class ITelescopeDriver (Interface):

    __options__ = {"device": "/dev/ttyS0",
                   "align_mode": ["POLAR", "ALT_AZ", "LAND"]}
 
class ITelescopeDriverSlew (Interface):

    __options__ = {"timeout": 10,
                   "auto_align": True,
                   "slew_idle_time": 0.1,
                   "max_slew_time": 60.0,
                   "max_slew_rate": [8, 2],                   
                   "stabilization_time": 2.0,
                   "position_sigma_delta": 60.0}
    # methods

    def open(self):
        pass

    def close(self):
        pass

    def slewToRaDec(self, ra, dec):
        pass

    def slewToAltAz(self, alt, az):
        pass

    def isSlewing (self):
        pass

    def abortSlew(self):
        pass

    def moveEast(self, offset):
        pass

    def moveWest(self, offset):
        pass

    def moveNorth(self, offset):
        pass

    def moveSouth(self, offset):
        pass

    def getRa(self):
        pass

    def getDec(self):
        pass

    def getAz(self):
        pass

    def getAlt(self):
        pass

    def getPosition(self):
        pass

    def getTarget(self):
        pass

    # events
    
    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass

class ITelescopeDriverSync(Interface):

    # methods
    def sync(self, coord):
        pass
    
    # events
    @event
    def syncComplete(self, position):
        pass

class ITelescopeDriverPark (Interface):

    __options__ = {"park_position_alt": 90.0,
                   "park_position_az": 180.0}
        
    # methods
    def park(self):
        pass

    def unpark(self):
        pass

    def setParkPosition (self, coord):
        pass

    # events
    @event
    def parkComplete(self, position):
        pass

    @event
    def unparkComplete (self):
        pass
