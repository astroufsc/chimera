#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.interface import Interface
from uts.core.event import event


class ICameraExpose(Interface):

    # config
    __options__ = {"driver" : "/Fake/camera"}
    
    # methods
    def expose (self, config):
        pass
    
    def abortExposure (self, config):
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

    # config
    __options__ = {"device"	         : "/dev/ttyS0",
                   "ccd"                 : ["imaging", "tracking"],
                   "exp_time"	         : (10, 600000),
                   "shutter" 	         : ["open", "close", "leave"],
                   "readout_aborted"     : True,
                   "readout_mode"	 : 1,
                   "date_format"	 : "%d%m%y",
                   "file_format"	 : "$num-$observer-$date-%objname",
                   "file_extension"  	 : "fits",
                   "directory"	         : "/home/someuser/images",
                   "save_on_temp"	 : False,
                   "seq_num"	         : 1,
                   "start_time"          : 0,
                   "observer"	         : "observer name",
                   "obj_name"	         : "object name"}

    
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

    def abortExposure(self, config):
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
