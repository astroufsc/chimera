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

class ITelescopeSlew(Interface):

    # properties
    
    currRA = 0
    currDec = 0
    currEphoc = 2000
    currAz = 0
    currAlt = 0
    cmdRA = 0
    cmdDec = 0
    cmdEphoc = 2000
    cmdAz = 0
    cmdAlt = 0
    axis = []
    slewRates = []
    slewRate = 0
    slewing = False

    # methods
    
    def slew(self, coord):
        pass

    def abortSlew(self):
        pass

    def moveAxis(self, axis, offset):
        pass

    # events

    @event
    def slewComplete(self, position, tracking, trackingRate):
        pass

    @event
    def abortComplete(self, position):
        pass

    @event
    def targetChanged(self, position):
        pass

class ITelescopeTracking(Interface):

    # properties
    trackingRates = []
    trackingRate = 0
    tracking = False

    # methods
    def setTracking(self, track, trackingRate):
        pass

    # events
    @event
    def trackingRateChanged(self, trackingRate):
        pass
         
class ITelescopeSync(Interface):

    # properties
    syncRa = 0
    syncDec = 0
    syncAz = 0
    syncAlt = 0

    # methods
    def sync(self, coord):
        pass
    
    # events
    @event
    def syncComplete(self, position):
        pass

class ITelescopePark(Interface):

    # properties
    parkRa = 0
    parkDec = 0
    parkAz = 0
    parkAlt = 0
    parking = 0
    
    # methods
    def park(self, coord = None):
        pass

    def unpark(self):
        pass

    # events
    @event
    def parkComplete(self, position):
        pass

class ITelescopeHome(Interface):

    # methods
    def findHome(self):
        pass
    
    # events
    @event
    def homeComplete(self, position):
        pass


