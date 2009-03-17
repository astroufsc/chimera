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
import urllib
import gzip
import os

import numpy as N
import pyfits

from chimera.interfaces.camera import (CCD, CameraFeature,
                                       ReadoutMode, Shutter)

from chimera.instruments.camera      import CameraBase
from chimera.instruments.filterwheel import FilterWheelBase

from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.lock       import lock


class FakeCamera (CameraBase, FilterWheelBase):

    __config__ = {"telescope"   : "/FakeTelescope/0",
                  "dome"        : "/FakeDome/0",
                  "use_dss"     : False,
                  "ccd_width"   : 1024,
                  "ccd_height"  : 1024}
    
    def __init__ (self):
        CameraBase.__init__ (self)
        FilterWheelBase.__init__ (self)

        self.__exposing = False
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

        self._ccds = {CCD.IMAGING: self._MY_CCD}

        self._adcs = {"12 bits": self._MY_ADC}

        self._binnings = {"1x1": self._MY_READOUT_MODE}

        self._binning_factors = {"1x1": 1}

        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: False,
                          CameraFeature.PROGRAMMABLE_FAN: False,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
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

    def __start__ (self):
        self["camera_model"] = "Fake Cameras Inc."
        self["ccd_model"] = "Fake CCDs Inc."

        self.setHz(2)

    def control (self):
        if self.isCooling():
            if self.__temperature > self.__setpoint:
                self.__temperature -= 0.5
            
        return True

    def _expose(self, imageRequest):
        
        self.__exposing = True
        self.exposeBegin(imageRequest)

        t=0
        self.__lastFrameStart = time.time()
        while t < imageRequest["exptime"]:
            if self.abort.isSet():
                self.__exposing = False
                return False
            
            time.sleep (0.1)            
            t+=0.1

        self.exposeComplete(imageRequest)
        self.__exposing = False
        return True
    
    def gunzip(self, file, newext):
        r_file = gzip.GzipFile(file, 'r')
        write_file = file + '.' + newext
        w_file = open(write_file, 'w')
        w_file.write(r_file.read())
        w_file.close()
        r_file.close()
                
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
        
    def _readout(self, imageRequest, aborted=False):
        
        pix = None
        telescope = None
        dome = None

        self.readoutBegin(imageRequest)
        
        try:
            telescope = self.getManager().getProxy(self['telescope'], lazy=True)
        except ObjectNotFoundException:
            pass

        try:
            dome = self.getManager().getProxy(self['dome'], lazy=True)
        except ObjectNotFoundException:
            pass
        
        if not telescope:
            self.log.debug("FakeCamera couldn't find telescope.")
        if not dome:
            self.log.debug("FakeCamera couldn't find dome.")

        ccd_width, ccd_height = self.getPhysicalSize()
        
        if (imageRequest["shutter"]==Shutter.CLOSE):
            self.log.info("Shutter closed -- making dark")
            pix = self.make_dark((ccd_height, ccd_width), N.float, imageRequest['exptime'])

        else:

            if telescope and dome:
                # use telescope/dome to get a real image from DSS if slit in right position

                self.log.debug("Dome open? "+ str(dome.isSlitOpen()))

                if dome.isSlitOpen() and self["use_dss"]:
                    domeAZ=dome.getAz().toD()
                    telAZ=telescope.getAz().toD()
                    if (telAZ < 3 and domeAZ > 357):
                        domeAZ-=360     #take care of wrap-around

                    self.log.debug("Dome AZ: "+str(domeAZ)+"  Tel AZ: "+str(telAZ))
                    if (abs(domeAZ-telAZ) <= 3):
                        self.log.debug("Dome & Slit aligned -- getting DSS")
                        url = "http://stdatu.stsci.edu/cgi-bin/dss_search?v=poss1_red&r=" + \
                              urllib.quote(telescope.getRa().strfcoord().replace(":"," ")) + \
                              "&d=" + urllib.quote(telescope.getDec().strfcoord().replace(":"," ")) + \
                              "&h=29&w=43.5&f=fits&c=gz&fov=NONE&v3="
                        self.log.debug("Attempting URL: "+url)
                        try:
                            dssfile=urllib.urlretrieve(url)[0]
                            self.gunzip(dssfile,'fits')
                            os.remove(dssfile)
                            dssfile+='.fits'
                            hdulist=pyfits.open(dssfile)
                            pix = hdulist[0].data
                            hdulist.close()
                            os.remove(dssfile)
                        except Exception, e:
                            self.log.warning("General error getting DSS image: " + str(e))
                        self.log.debug("Making flat...")
                        try:
                            pix *= (self.make_flat(pix.shape, N.float)/1000)
                        except Exception, e:
                            self.log.warning("Error generating flat: " + str(e))
                        self.log.debug("Generating dark...")
                        try:
                            pix += self.make_dark(pix.shape, N.float, imageRequest['exptime'])
                        except Exception, e:
                            self.log.warning("Error generating dark: " + str(e))

            # without telescope/dome, or if dome/telescope aren't aligned, or the dome is closed
            # or we otherwise failed, just make a flat pattern with dark noise
            if (pix == None):
                try:
                    self.log.info("Making simulated flat image: " + str(ccd_height) + "x" + str(ccd_width))
                    self.log.debug("Generating dark...")
                    pix = self.make_dark((ccd_height,ccd_width), N.float, imageRequest['exptime'])
                    self.log.debug("Making flat...")
                    pix += self.make_flat((ccd_height,ccd_width), N.float)
                except Exception, e:
                    self.log.warning("MakekFlat error: " + str(e))
        
        # Last resort if nothing else could make a picture
        if (pix == None):
            pix = N.zeros((100,100), dtype=N.int32)

        proxy = self._saveImage(imageRequest, pix, {"frame_start_time": self.__lastFrameStart})

        self.readoutComplete(proxy)
        return proxy

    def isExposing(self):
        return self.__exposing

    @lock
    def startCooling(self, setpoint):
        self.__cooling = True
        self.__setpoint = setpoint
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
    
    def getSetPoint(self):
        return self.__setpoint

    @lock
    def startFan(self, rate=None):
        self.__isFanning = True

    @lock
    def stopFan(self):
        self.__isFanning = False

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
        self.filterChange(filter, self.__lastFilter)
        self.__lastFilter = filter

