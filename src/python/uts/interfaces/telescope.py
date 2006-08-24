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
