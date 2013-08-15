#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  
#
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
import datetime as dt
import random
import urllib
import os
import shutil
import ctypes

import numpy as N
import pyfits

from chimera.instruments.apogee.apogeemanager import ApogeeManager
from chimera.interfaces.camera import (CCD, CameraFeature, Shutter, ReadoutMode, CameraStatus)

from chimera.util.image import Image, ImageUtil, WCSNotFoundException

from chimera.instruments.camera      import CameraBase
from chimera.instruments.filterwheel import FilterWheelBase, InvalidFilterPositionException

from chimera.core.lock       import lock

class APOGEE(CameraBase, FilterWheelBase): 

    #  por mais que nao utilize esse __config__ mas parece que esta bem preso as classes Base
    #entao deixa assim, porque senao nao funciona
    __config__ = {"use_dss"     : True,
                  "ccd_width"   : 512,
                  "ccd_height"  : 512}

    def __init__ (self):
        CameraBase.__init__ (self)
        FilterWheelBase.__init__ (self)

        self.__apogee_manager = ApogeeManager()

        self.__cooling  = False

        self.__lastFilter = self._getFilterName(0)
        self.__temperature = 20.0
        self.__setpoint = 0
        self.__lastFrameStart = 0
        self.__isFanning = False

        # my internal CCD code
        self._MY_CCD = 1 << 1
        self._MY_ADC = 1 << 2
        self._MY_READOUT_MODE = 1 << 3

        self._ccds = {self._MY_CCD: CCD.IMAGING}

        self._adcs = {"12 bits": self._MY_ADC}

        self._binnings = {"1x1": self._MY_READOUT_MODE}

        self._binning_factors = {"1x1": 1}

        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: False,
                          CameraFeature.PROGRAMMABLE_FAN: True,
                          CameraFeature.PROGRAMMABLE_LEDS: False,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}
        
        readoutMode = ReadoutMode()
        readoutMode.mode = 0
        readoutMode.gain = 1.0
        readoutMode.width = 1024
        readoutMode.height = 1024
        readoutMode.pixelWidth = 9.0
        readoutMode.pixelHeight = 9.0

        self._readoutModes = {self._MY_CCD:
                                  {self._MY_READOUT_MODE: readoutMode}}

        #  TODO : necessario?
        self._binning_factors = {"1x1": 1,
                                 "2x2": 2,
                                 "3x3": 3,
                                 "9x9": 9}                                  

    def __del__ (self):
        self.__apogee_manager.stop()

    def __start__ (self):
        self["camera_model"] = "Alta U16M"
        self["ccd_model"] = "Apogee Instruments Inc."
        self.__apogee_manager.setUp()

    def control (self):
        # if self.isCooling():
        #     if self.__temperature > self.__setpoint:
        #         self.__temperature -= 0.5
            
        return True

    def _expose(self, imageRequest):
        self.log.debug("apogee - expose - BEGIN")

        shutterRequest = imageRequest['shutter']

        # '~/images/$LAST_NOON_DATE/$DATE-$TIME.fits')
        filenameRequest = ImageUtil.makeFilename( imageRequest['filename'] )
	imageRequest['filenameRequest'] = filenameRequest
        file(filenameRequest, "w").close()

        exptimeRequest = imageRequest["exptime"]
        self.log.debug("shutterRequest = %s" % shutterRequest)
        self.log.debug("filenameRequest = %s" % filenameRequest)
        self.log.debug("exptime = %s" % exptimeRequest)

	#  0 = false
	shutter = 0
        if shutterRequest == Shutter.OPEN:
            shutter = 1
        elif shutterRequest == Shutter.CLOSE:
            shutter = 0
	
        self.log.debug("shutter = %d" % shutter )

        self.exposeBegin(imageRequest)
        self.__apogee_manager.expose(filenameRequest, int(exptimeRequest), int(shutterRequest) )

        # if any error happens, it will be thrown an exception
        status = CameraStatus.OK

        # save time exposure started
        self.lastFrameStartTime = dt.datetime.utcnow()
        self.lastFrameTemp = self.__apogee_manager.getTemperature()

        self.exposeComplete(imageRequest, status)
        self.log.debug("apogee - expose - END")
    
    def make_dark(self, shape, dtype, exptime):
        ret = N.zeros(shape, dtype=dtype)
        #Taken from specs for KAF-1603ME as found in ST-8XME
        #normtemp is now in ADU/pix/sec
        normtemp= ((10 * 2**((self.__temperature-25)/6.3)) * exptime)/2.3
        ret += normtemp + N.random.random(shape)  # +/- 1 variance in readout
        return ret

    def make_flat(self, shape, dtype):

        """
        Flat is composition of:
         - a normal distribution of mean=1000, sigma=1
         - plus a pixel sensitivity constant, which is axis dependent
         - plus a bad region with different mean level
        """

        iadd=15.0/shape[0]
        jadd=10.0/shape[1]

        badlevel = 0

        badareai=shape[0]/2
        badareaj=shape[1]/2

        # this array is only to make sure we create our array with the right dtype
        ret  = N.zeros(shape, dtype=dtype)

        ret += N.random.normal(1000, 1, shape)
        ret += N.fromfunction(lambda i,j: i*jadd - j*jadd, shape)

        ret[badareai:,badareaj:] += badlevel

        return ret
        
    def _readout(self, imageRequest):
        self.log.debug("apogee - _readout - BEGIN")
        (mode, binning, top,  left,
         width, height) = self._getReadoutModeInfo(imageRequest["binning"],
                                                   imageRequest["window"])
        # readout 
        img = N.zeros((height, width), N.int32)

        self.readoutBegin(imageRequest)

        self.log.debug("apogee - _readout - temperature = %f" % self.lastFrameTemp)
        self.log.debug("apogee - _readout - start_time = %s" % self.lastFrameStartTime)

        img = self.__apogee_manager.getImageData()

        proxy = self._saveImage(imageRequest, img,
                                {"frame_temperature": self.lastFrameTemp,
                                 "frame_start_time": self.lastFrameStartTime,
                                 "binning_factor":self._binning_factors[binning]})

        self.log.debug("apogee - _readout - END")
        return True

    @lock
    def startCooling(self, setpoint):
        self.__cooling = True
        self.__setpoint = setpoint
        self.__apogee_manager.startCooling(setpoint)
        return True

    @lock
    def stopCooling(self):
        self.__cooling = False
        self.__apogee_manager.stopCooling()
        return True

    def isCooling(self):
        return self.__cooling

    @lock
    def getTemperature(self):
        self.log.debug("apogee - temperature = %s ºC" % self.__apogee_manager.getTemperature()) 
        return self.__apogee_manager.getTemperature()
    
    def getSetPoint(self):
        return self.__setpoint

    @lock
    def startFan(self, rate=None):
        self.__isFanning = True
        self.__apogee_manager.startFan()

    @lock
    def stopFan(self):
        self.__isFanning = False
        self.__apogee_manager.stopFan()

    def isFanning(self):
        self.__isFanning
    
    def getCCDs(self):
        return self._ccds

    def getCurrentCCD(self):
        return self._MY_CCD

    def getBinnings(self):
        return self._binnings

    def getADCs(self):
        return self._adcs

    def getPhysicalSize(self):
        return (self["ccd_width"], self["ccd_height"])

    def getPixelSize(self):
        return (9,9)

    def getOverscanSize(self, ccd=None):
        return (0, 0)

    def getReadoutModes(self):
        return self._readoutModes

    def supports(self, feature=None):
        return self._supports[feature]

    #
    # filter wheel
    #
    def getFilter (self):
        return self.__lastFilter

    @lock
    def setFilter (self, filter):
        if filter not in self.getFilters():
            raise InvalidFilterPositionException("%s is not a valid filter" % filter)

        self.filterChange(filter, self.__lastFilter)
        self.__lastFilter = filter

