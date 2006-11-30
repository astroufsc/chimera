#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.interface import Interface
from uts.core.event import event

class ICameraExpose(Interface):

    # methods
    def expose (self, config):
        pass
    
    def abortExposure (self, readout = True):
        pass

    # events
    @event
    def exposeComplete (self):
        pass

    @event
    def exposeAborted (self):
        pass

    @event
    def readoutComplete (self):
        pass

class ICameraTemperture(Interface):

    # methods
    def setTemperture(self, double):
        pass

    def setCooler(self, on, power):
        pass

    # events
    @event
    def temperture(self, threshold):
        pass


class ICameraDriver(Interface):

    # methods

    def open(self, device):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    def exposing(self):
        pass

    def espose(self, config):
        pass

    def abortExposure(self, readout = True):
        pass

    # events
    @event
    def exposeComplete (self):
        pass

    @event
    def exposeAborted (self):
        pass

    @event
    def readoutComplete (self):
        pass
