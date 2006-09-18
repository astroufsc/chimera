#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

class TelescopeSlew(object):

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

    def slewComplete(self, position, tracking, trackingRate):
        pass

    def abortComplete(self, position):
        pass

    def targetChanged(self, position):
        pass

class TelescopeTracking(object):

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
         
class TelescopeSync(object):

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

class TelescopePark(object):

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

class TelescopeHome(object):

    # methods
    def findHome(self):
        pass
    
    # events
    @event
    def homeComplete(self, position):
        pass


