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

from chimera.interfaces.camera import Shutter, Binning, Window

from chimera.util.enum import Enum


Bitpix = Enum("char8", "uint16", "int16", "int32", "int64", "float32", "float64")

Device = Enum ("USB",
               "USB1",
               "USB2",
               "LPT"
               "LPT1",
               "LPT2")

CCD = Enum ("IMAGING",
            "TRACKING")


class ICameraDriver(Interface):

    # config
    __config__ = {"device"	     : Device.USB,
                  "ccd"              : CCD.IMAGING,
                  
                  "exp_time"         : (0.0, 216000.0), # seconds
                  "shutter" 	     : Shutter.OPEN,

                  "readout_aborted"  : True,

                  "temp_setpoint"    : 20.0,
                  "temp_delta"       : 1.0,
                  
                  # drivers should use SaveImage utility class to
                  # handles this values according to the semantics
                  # defined in ICameta spec.
                  "window_x"         : 0.5,
                  "window_y"         : 0.5,
                  "window_width"     : 1.0,
                  "window_height"    : 1.0,

                  "binning"	     :  Binning._1x1,
                  #"gain"            : 1.0,
                  
                  # FITS generation parameters
                  "date_format"	     : "%d%m%y-%H%M%S",
                  "file_format"	     : "$date",
                  "file_extension"   : "fits",
                  "directory"	     : "$HOME/images", # environment variables allowed
                  "save_on_temp"     : True,
                  "bitpix"           : Bitpix.int16,
                  }
                  
    # methods

    def open(self, device):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    def isExposing(self):
        pass

    def expose(self):
        pass

    def abortExposure(self):
        pass

    def startCooling(self):
        pass

    def stopCooling(self):
        pass

    def isCooling(self):
        pass

    def getTemperature(self):
        pass

    def getSetpoint(self):
        pass

    # events
    @event
    def exposeBegin (self, exp_time):
        pass
    
    @event
    def exposeComplete (self):
        pass

    @event
    def readoutBegin (self, filename):
        pass

    @event
    def readoutComplete (self, filename):
        pass

    @event
    def abortComplete (self):
        pass

    @event
    def temperatureChange(self, newTemp, delta):
        pass
    
