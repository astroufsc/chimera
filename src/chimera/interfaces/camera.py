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


class ICameraTemperature(Interface):

    # methods
    def setTemperature(self, config):
        pass

    def getTemperature(self):
        pass

    # events
    @event
    def temperatureChanged(self, newTemp, oldTemp):
        pass


class ICameraDriver(Interface):

    # config
    __options__ = {"device"	         : "usb",
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
                   "obj_name"	         : "object name",
                   "temp_regulation"     : True,
                   "temp_setpoint"       : 20.0,
                   "temp_delta"          : 1.0,
                   "auto_freeze"         : False}
    
    # methods

    def open(self, device):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    def exposing(self):
        pass

    def expose(self, config):
        pass

    def abortExposure(self, config):
        pass

    def setTemperature(self, config):
        pass

    def getTemperature(self):
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

    @event
    def temperatureChanged(self, newTemp, oldTemp):
        pass
    
