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

import time
import random
import threading

from chimera.interfaces.cameradriver      import ICameraDriver
from chimera.interfaces.filterwheeldriver import IFilterWheelDriver

from chimera.core.chimeraobject      import ChimeraObject

from chimera.util.imagesave import ImageSave

from chimera.core.lock import lock


class FakeCamera (ChimeraObject, ICameraDriver, IFilterWheelDriver):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self.__exposing = False
        self.__cooling  = False

        self.__abort = threading.Event()

        self._lastFilter = 0

    def __start__ (self):
        self.setHz(1.0/10)

    def open(self, device):
        return True

    def close(self):
        return True

    def control (self):
        self.temperatureChange(20*random.random(), 0.1)
        return True

    def ping(self):
        return True

    def isExposing(self):
        return self.__exposing

    @lock
    def expose(self):
        self.__exposing = True
        self.__abort.clear()

        self.exposeBegin(self["exp_time"])

        t=0
        while t < self["exp_time"]:
            if self.__abort.isSet():
                self.__exposing = False
                return
            
            time.sleep (0.1)            
            t+=0.1

        self.exposeComplete()

        next_filename = ImageSave.save(None, 
                                       self["directory"],
                                       self["file_format"],
                                       self["file_extension"],
                                       self["date_format"],
                                       None,
                                       self["bitpix"],
                                       self["save_on_temp"],
                                       dry=True)


        self.readoutBegin(next_filename)
        
        t=0
        while t < 1: # really fast CCD :)
            if self.__abort.isSet():
                self.__exposing = False
                return
            
            time.sleep (0.1)            
            t+=0.1

        self.readoutComplete(next_filename)
        
        self.__exposing = False
        return self["file_format"]

    @lock
    def abortExposure(self):

        if not self.isExposing(): return

        self.__abort.set()

        if self["readout_aborted"]:
            self.readoutBegin(self["file_format"])
            time.sleep(1)
            self.readoutComplete(self["file_format"])

        # busy waiting for exposure stops
        while self.isExposing(): time.sleep(0.1)
            
        self.abortComplete()

    @lock
    def startCooling(self):
        self.__cooling = True
        return True

    @lock
    def stopCooling(self):
        self.__cooling = False
        return True

    def isCooling(self):
        return self.__cooling

    def getTemperature(self):
        return 20 * random.random()

    @lock
    def getFilter (self):
        return self._lastFilter

    @lock
    def setFilter (self, filter):
        self.filterChange(filter, self._lastFilter)
        self._lastFilter = filter
