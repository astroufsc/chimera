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

import os
import time
import logging
import threading

import numpy as N
        
from sbigdrv import *

from chimera.core.chimeraobject            import ChimeraObject
from chimera.interfaces.cameradriver       import ICameraDriver, CCD, Device, Bitpix
from chimera.interfaces.camera             import Shutter, Binning
from chimera.interfaces.filterwheeldriver  import IFilterWheelDriver

from chimera.core.lock import lock

from chimera.util.imagesave import ImageSave


class SBIG(ChimeraObject, ICameraDriver, IFilterWheelDriver):  

    def __init__(self):
        ChimeraObject.__init__ (self)

        self.drv = SBIGDrv()
        self.ccd = SBIGDrv.imaging
        self.dev = SBIGDrv.usb

        self.lastTemp = 0
        self.lastFilter = None

        self.lastFrameStartTime = 0
        self.lastFrameFilename = ""

        self.term = threading.Event()

        self.setHz(1.0/5)

    def __start__ (self):

        if self['ccd'] == CCD.IMAGING:
            self.ccd = SBIGDrv.imaging
        else:
            self.ccd = SBIGDrv.tracking
           
        if self['device'] == Device.USB:
            self.dev = SBIGDrv.usb
        else:
            self.dev = SBIGDrv.lpt1

	self["bitpix"] = Bitpix.uint16
                        
	self["bitpix"] = Bitpix.uint16
                        
        return self.open(self.dev)

    def __stop__ (self):
        self.close ()

    def control (self):

        #FIXME disabled to get more tests
        return False

        try:
            temp = self.drv.getTemperature ()

            newTemp = temp[3]

            if (newTemp - self.lastTemp) >= self['temp_delta']:
                self.temperatureChange (newTemp, self.lastTemp-newTemp)
                self.lastTemp = newTemp
            
        except SBIGException, e:
            self.log.exception("something wrong, will try again on the next loop.")

        return True # to continue pooling

    @lock
    def open(self, device):
        self.drv.openDriver()
        self.drv.openDevice(device)
        self.drv.establishLink()
        self.drv.queryCCDInfo()

        return True

    @lock
    def close(self):
        try:
            self.drv.closeDevice()
            self.drv.closeDriver()
        except SBIGException:
            pass

    @lock
    def ping(self):
        return self.drv.isLinked()

    def isExposing(self):
        return self.drv.exposing(self.ccd)

    @lock
    def expose(self):

        self.term.clear()

        if self._expose():
            return self._readout(aborted=False)
        else:
            return False

    def abortExposure(self):

        if not self.isExposing():
            return False

        # set our event, so current exposure know that it must abort
        self.term.set()

        while self.isExposing():
            time.sleep (0.1)

        self.abortComplete()

        return True

    # methods
    @lock
    def startCooling(self):
        self.drv.setTemperature (True,
                                 self["temp_setpoint"])
        return True

    @lock
    def stopCooling(self):
        self.drv.setTemperature (False,
                                 self["temp_setpoint"])

        return True

    @lock
    def isCooling(self):
        return bool(self.drv.getTemperature()[0])

    @lock
    def getTemperature(self):
        return self.drv.getTemperature()[-1]

    @lock
    def getSetpoint(self):
        return self.drv.getTemperature()[-2]

    @lock
    def getFilter (self):
        # Chimera uses filter starting with 0
        position = self.drv.getFilterPosition()
        if position == 0: return -1 # unknown
        return position-1

    @lock
    def setFilter (self, filter):
        # Chimera uses filter starting with 0
        position = self.drv.filters.get(filter+1, None)

        if not position:
            raise ValueError("Selected filter not defined on SBIG driver.")

        if self.lastFilter == None:
            self.lastFilter = self.getFilter()

        self.drv.setFilterPosition (position)
        
        while self.drv.getFilterStatus() != 1: # while not idle
            time.sleep(.5)

        self.filterChange(filter, self.lastFilter)
        self.lastFilter = filter

        return True
        
    def _expose(self):

        if self["shutter"] == Shutter.OPEN:
            shutter = SBIGDrv.openShutter
        elif self["shutter"] == Shutter.CLOSE:
            shutter = SBIGDrv.closeShutter
        elif self["shutter"] == Shutter.LEAVE:
            shutter = SBIGDrv.leaveShutter
        else:
            raise ValueError("Incorrect shutter option (%s). Leaving shutter intact" % self["shutter"])
            shutter = SBIGDrv.leaveShutter

        # ok, start it
        self.exposeBegin(self["exp_time"])
        
        self.drv.startExposure(self.ccd, int(self["exp_time"]*100), shutter)
        
        # save time exposure started
        self.lastFrameStartTime = time.time()

        while self.isExposing():
                                        
            # check if user asked to abort
            if self.term.isSet():
                # ok, abort and check if user asked to do a readout anyway

                if self.isExposing():
                    self._endExposure()
                
                if self["readout_aborted"]:
                    self._readout(aborted=True)
                    
                return False

        # end exposure and returns
        return self._endExposure()

    def _endExposure(self):
        self.drv.endExposure(self.ccd)

        # fire exposeComplete event
        self.exposeComplete()

        return True

    def _readout(self, aborted=False):

        #readoutMode = self._getReadoutMode(self["window_width"],
        #                                   self["window_height"], self["binning"])
        
        readoutMode = self.drv.readoutModes[self.ccd][0]
        
        img = N.zeros(readoutMode.getSize(), N.int32)
        
        # start readout
        #img = ImageSave.getPixels(readoutMode,
        #                          self["window_width"], self["window_height"],
        #                          self["bitpix"])

        # convert the matrix to SBIG specific window and line specification
        #window, line = self._getWindowAndLine(img)

        try:
            next_filename = ImageSave.save(None, 
                                           self["directory"],
                                           self["file_format"],
                                           self["file_extension"],
                                           self["date_format"],
                                           self.lastFrameStartTime,
                                           self["bitpix"],
                                           self["save_on_temp"],
                                           dry=True)
        except Exception, e:
            print e

        self.readoutBegin(next_filename)

        self.drv.startReadout(self.ccd, 0)
        
        for line in range(readoutMode.height):
	
            img[line] = self.drv.readoutLine(self.ccd, 0)

            # check if user asked to abort
            if not aborted and self.term.isSet():
                self._endReadout(next_filename)
                return self._saveFITS(img)

        # end readout and save
        self._endReadout(next_filename)
        return self._saveFITS(img)

    # TODO
    def _getWindowAndLine(self, img):
        shape = img.shape()
        return ()

    def _getReadoutMode(self, width, height, binning):
        """
        Given width, height and binning get a
        """

        for i, mode in self.drv.readoutModes[self.ccd].items():
            print i, mode

        return None

    def _saveFITS(self, img):

        try:
            self.lastFrameFilename = ImageSave.save(img,
                                                    self["directory"],
                                                    self["file_format"],
                                                    self["file_extension"],
                                                    self["date_format"],
                                                    self.lastFrameStartTime,
                                                    self["bitpix"],
                                                    self["save_on_temp"])
        except Exception, e:
            print e
            
        return self.lastFrameFilename


    def _endReadout(self, filename):
        
        self.drv.endReadout(self.ccd)
        self.readoutComplete(filename)
        
        return True
