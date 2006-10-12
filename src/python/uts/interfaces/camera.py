#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.interface import Interface
from uts.core.event import event

class ICameraExpose(Interface):

    # properties
    expTime = 0
    nExp = 0
    window = None
    binning  = 0
    binningList = []
    gain = 0
    gainList = []
    chipSize = None
    pixelSize = None
    maxADU = 0
    fullWellCapacity = 0
    exposing = False

    # methods
    def expose (self, expTime, nexp):
        pass
    
    def abortExposure (self):
        pass

    def stopExposure (self):
        pass

    # events
    @event
    def exposeComplete (self):
        pass

    @event
    def exposeAborted (self):
        pass

    @event
    def exposeStopped (self):
        pass


class ICameraTemperture(Interface):

    # properties
    cooler = False
    coolerPower = 1.0
    ccdTemperature = 0.0
    ambientTemperature = 0.0

    # methods
    def setTemperture(self, double):
        pass

    def setCooler(self, on, power):
        pass

    # events
    @event
    def temperture(self, threshold):
        pass
