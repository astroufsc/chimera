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
import sys

from chimera.interfaces.cameradriver      import ICameraDriver
from chimera.interfaces.filterwheeldriver import IFilterWheelDriver

from chimera.core.chimeraobject      import ChimeraObject
from chimera.core.exceptions import ChimeraException

from chimera.util.imagesave import ImageSave

from chimera.core.lock import lock


class FakeCamera (ChimeraObject, ICameraDriver, IFilterWheelDriver):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self.__exposing = False
        self.__cooling  = False

        self.__abort = threading.Event()

        self.__lastFilter = 0

        self.__temperature = 20.0

    def __start__ (self):
        self.setHz(2)

    def open(self, device):
        return True

    def close(self):
        return True

    def control (self):
        if self.isCooling():
            self.__temperature -= 1.5
            
        return True

    def ping(self):
        return True

    def isExposing(self):
        return self.__exposing

    @lock
    def expose(self):
        self.__exposing = True
        self.__abort.clear()

        ret = ()

        # normal exposure
        if self._expose():
            ret = self._readout()

        self.__exposing = False
        return ret

    def _expose(self):
        
        self.exposeBegin(self["exp_time"])

        t=0
        while t < self["exp_time"]:
            if self.__abort.isSet():
                return self["readout_aborted"]
            
            time.sleep (0.1)            
            t+=0.1

        self.exposeComplete()
        return True

    def _readout(self):

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

        time.sleep (2)            

        try:
            fp = open(next_filename, "w")
            print >> fp, "Nice image! - %s" % next_filename
        except IOError, e:
            raise ChimeraException("Couldn't save image %s (%s)" % (next_filename, e.strerror))

        self.readoutComplete(next_filename)
        
        return next_filename

    def abortExposure(self):

        if not self.isExposing(): return

        self.__abort.set()

        # busy waiting for exposure/readout stops
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

    @lock
    def getTemperature(self):
        return self.__temperature + random.random()

    def getFilter (self):
        return self.__lastFilter

    @lock
    def setFilter (self, filter):
        self.filterChange(filter, self.__lastFilter)
        self.__lastFilter = filter
