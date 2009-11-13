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

from __future__ import division

import time
import datetime as dt
import numpy as N
        
from chimera.instruments.sbig.sbigdrv import (SBIGDrv, SBIGException)

from chimera.interfaces.camera   import (CCD, CameraFeature, Shutter, CameraStatus)

from chimera.instruments.camera      import CameraBase
from chimera.instruments.filterwheel import FilterWheelBase

from chimera.core.lock import lock


class SBIG(CameraBase, FilterWheelBase):  

    def __init__(self):
        CameraBase.__init__ (self)
        FilterWheelBase.__init__ (self)

        self.drv = SBIGDrv()
        self.ccd = SBIGDrv.imaging
        self.dev = SBIGDrv.usb

        self.lastTemp = 0
        self.lastFilter = None

        self.lastFrameStartTime = 0
        self.lastFrameTemp = None
        self.lastFrameFilename = ""

        self._isFanning = False

        self.setHz(1.0/5)

        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: False,
                          CameraFeature.PROGRAMMABLE_FAN: False,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

        self._ccds = {SBIGDrv.imaging: CCD.IMAGING,
                      SBIGDrv.tracking: CCD.TRACKING}

        self._adcs = {"12 bits": 0}

        self._binnings = {"1x1": 0,
                          "2x2": 1,
                          "3x3": 2,
                          "9x9": 9}


        self._binning_factors = {"1x1": 1,
                                 "2x2": 2,
                                 "3x3": 3,
                                 "9x9": 9}

    def __start__ (self):

        if self['ccd'] == CCD.IMAGING:
            self.ccd = SBIGDrv.imaging
        else:
            self.ccd = SBIGDrv.tracking

        self.open(self.dev)

        # make sure filter wheel is in the right position
        self.setFilter(self.getFilters()[0])
        self.startCooling(self.getSetPoint())
        self.startFan()

        self["camera_model"] = self.drv.cameraNames[self.ccd]

    def __stop__ (self):
        try:
            self.stopFan()
            self.stopCooling()
            self.close ()
        except SBIGException: pass

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

    @lock
    def startCooling(self, tempC):
        self.drv.setTemperature (True, tempC)
        return True

    @lock
    def stopCooling(self):
        self.drv.setTemperature (False, self.getSetPoint())
        return True

    @lock
    def isCooling(self):
        return bool(self.drv.getTemperature()[0])

    @lock
    def getTemperature(self):
        return self.drv.getTemperature()[-1]

    @lock
    def getSetPoint(self):
        return self.drv.getTemperature()[-2]

    @lock
    def startFan(self, rate=None):
        self.drv.startFan()
        self._isFanning = True

    @lock
    def stopFan(self):
        self.drv.stopFan()
        self._isFanning = False

    def isFanning(self):
        return self._isFanning

    def getFilter (self):
        # SBIG support for this is very poor, we just keep track mannualy
        return self.lastFilter

    @lock
    def setFilter (self, filter):
        # Chimera uses filter starting with 0, and SBIG uses 1
        position = self.drv.filters.get(self._getFilterPosition(filter)+1, None)

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

    def getCCDs(self):
        return self._ccds

    def getCurrentCCD(self):
        return self.ccd

    def getBinnings(self):
        return self._binnings

    def getADCs(self):
        return self._adcs

    def getPhysicalSize(self):
        return self.drv.readoutModes[self.ccd][0].getSize()

    def getPixelSize(self):
        return self.drv.readoutModes[self.ccd][0].getPixelSize()

    def getOverscanSize(self):
        return (0,0)

    def getReadoutModes(self):
        return self.drv.readoutModes

    def supports(self, feature=None):
        return self._supports[feature]

    def _expose(self, imageRequest):
        
        shutterRequest = imageRequest['shutter']
        
        if shutterRequest == Shutter.OPEN:
            shutter = SBIGDrv.openShutter
        elif shutterRequest == Shutter.CLOSE:
            shutter = SBIGDrv.closeShutter
        elif shutterRequest == Shutter.LEAVE_AS_IS:
            shutter = SBIGDrv.leaveShutter
        else:
            self.log.warning("Incorrect shutter option (%s)."
                             " Leaving shutter intact" % shutterRequest)
            shutter = SBIGDrv.leaveShutter
        
        # ok, start it
        self.exposeBegin(imageRequest)
        
        self.drv.startExposure(self.ccd,
                               int(imageRequest["exptime"]*100), shutter)
        
        # save time exposure started
        self.lastFrameStartTime = dt.datetime.utcnow()
        self.lastFrameTemp = self.getTemperature()

        status = CameraStatus.OK
        while self.drv.exposing(self.ccd):
            # [ABORT POINT]
            if self.abort.isSet():
                status = CameraStatus.ABORTED
                break
            # this sleep is EXTREMELY important: without it, Python would stuck on this
            # thread and abort will not work.
            time.sleep(0.01)

        # end exposure and returns
        return self._endExposure(imageRequest, status)

    def _endExposure(self, request, status):
        self.drv.endExposure(self.ccd)
        self.exposeComplete(request, status)
        return True

    def _readout(self, imageRequest):

        (mode, binning, top,  left,
         width, height) = self._getReadoutModeInfo(imageRequest["binning"],
                                                   imageRequest["window"])
        # readout 
        img = N.zeros((height, width), N.int32)

        self.readoutBegin(imageRequest)

        self.drv.startReadout(self.ccd, mode.mode, (top, left, width, height))
        
        for line in range(height):
            # [ABORT POINT]
            if self.abort.isSet():
                self._endReadout(None, CameraStatus.ABORTED)
                return False
 
            img[line] = self.drv.readoutLine(self.ccd, mode.mode, (left, width))


        proxy = self._saveImage(imageRequest, img,
                                {"frame_temperature": self.lastFrameTemp,
                                 "frame_start_time": self.lastFrameStartTime,
                                 "binning_factor":self._binning_factors[binning]})

        return self._endReadout(proxy, CameraStatus.OK)

    def _endReadout(self, proxy, status):
        self.drv.endReadout(self.ccd)
        self.readoutComplete(proxy, status)
        return proxy

    def getMetadata(self, request):
        headers = []
        headers += super(CameraBase, self).getMetadata(request)
        headers += super(FilterWheelBase, self).getMetadata(request)
        return headers

