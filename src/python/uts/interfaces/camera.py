#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

class CameraExpose(object):

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
    def exposeComplete (self):
        pass

    def exposeAborted (self):
        pass

    def exposeStopped (self):
        pass

