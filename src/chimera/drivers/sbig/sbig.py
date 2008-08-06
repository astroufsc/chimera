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

import os
import time
import logging
import threading
from math import pi
import numpy as N
        
from sbigdrv import *

from chimera.core.chimeraobject            import ChimeraObject
from chimera.interfaces.cameradriver       import (ICameraDriver, CCD,
                                                   Device, CameraFeature)
from chimera.interfaces.camera             import Shutter
from chimera.interfaces.filterwheeldriver  import IFilterWheelDriver

from chimera.core.lock import lock

from chimera.controllers.imageserver.image import Image


class SBIG(ChimeraObject, ICameraDriver, IFilterWheelDriver):  

    def __init__(self):
        ChimeraObject.__init__ (self)

        self.drv = SBIGDrv()
        self.ccd = SBIGDrv.imaging
        self.dev = SBIGDrv.usb

        self.lastTemp = 0
        self.lastFilter = None

        self.lastFrameStartTime = 0
        self.lastFrameTemp = None
        self.lastFrameFilename = ""

        self.term = threading.Event()

        self.setHz(1.0/5)

        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: False,
                          CameraFeature.PROGRAMMABLE_FAN: False,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

        self._ccds = {CCD.IMAGING: SBIGDrv.imaging,
                      CCD.TRACKING: SBIGDrv.tracking}

        self._adcs = {"12 bits": 0}

        self._binnings = {"1x1": 0,
                          "2x2": 1,
                          "3x3": 2,
                          "9x9": 9}

        self._binning_factors = {"1x1": 1,
                                 "2x2": 2,
                                 "3x3": 3,
                                 "4x4": 4}

    def __start__ (self):

        if self['ccd'] == CCD.IMAGING:
            self.ccd = SBIGDrv.imaging
        else:
            self.ccd = SBIGDrv.tracking

        if self['device'] == Device.USB:
            self.dev = SBIGDrv.usb
        else:
            self.dev = SBIGDrv.lpt1

        self.open(self.dev)

        # make sure filter wheel is in the right position
        self.setFilter(0)
        self.startCooling(self.getSetpoint())
        self.startFan()

    def __stop__ (self):
        self.stopFan()
        self.stopCooling()
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

    @lock
    def isExposing(self):
        return self.drv.exposing(self.ccd)

    @lock
    def expose(self, imageRequest):

        self.term.clear()

        if self._expose(imageRequest):
            return self._readout(imageRequest, aborted=False)
        else:
            return False

    def abortExposure(self, readout=True):

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
    def startCooling(self, tempC):
        self.drv.setTemperature (True, tempC)
        return True

    @lock
    def stopCooling(self):
        self.drv.setTemperature (False, self.getSetpoint())
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
    def startFan(self, rate=None):
        self.drv.startFan()
        self._isFanning = True

    @lock
    def stopFan(self):
        self.drv.stopFan()
        self._isFanning = False

    def isFanning(self):
        return self.drv.isFanning()

    @lock
    def getFilter (self):
        # SBIG support for this is very poor, we just keep track mannualy
        return self.lastFilter

    @lock
    def setFilter (self, filter):
        # Chimera uses filter starting with 0, and SBIG uses 1
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


    def getCCDs(self):
        return self._ccds

    def getCurrentCCD(self):
        return self["ccd"]

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
        self.exposeBegin(imageRequest["exp_time"])
        
        self.drv.startExposure(self.ccd, int(imageRequest["exp_time"]*100), shutter)
        
        # save time exposure started
        self.lastFrameStartTime = time.gmtime()
        self.lastFrameTemp = self.getTemperature()
        
        while self.isExposing():
                                        
            # check if user asked to abort
            if self.term.isSet():
                # ok, abort and check if user asked to do a readout anyway

                if self.isExposing():
                    self._endExposure()
                
                #TODO: Support aborted readout
                #if self["readout_aborted"]:
                #    self._readout(aborted=True)
                    
                return False

        # end exposure and returns
        return self._endExposure()

    def _endExposure(self):
        self.drv.endExposure(self.ccd)
        self.exposeComplete()
        return True

    def _readout(self, imageRequest, aborted=False):

        try:
            mode, binning, top, left, width, height = self._getReadoutMode(imageRequest)
        except TypeError, e:
            self.log.warning("Invalid subframe %s. "
                             "Using full frame, no-binning, just to don't loose your data."%imageRequest["window"])
            self.log.warning(e)
            mode = self.drv.readoutModes[self.ccd][0]
            top = left = 0
            binning = "1x1"
            width, height = mode.width, mode.height
        
        # readout 
        img = N.zeros((height, width), N.int32)

        self.readoutBegin(imageRequest)

        self.drv.startReadout(self.ccd, mode.mode, (top,left,width,height))
        
        for line in range(height):
            
            img[line] = self.drv.readoutLine(self.ccd, mode.mode, (left, width))

            #TODO: Handle readout abort
            ## check if user asked to abort
            #if not aborted and self.term.isSet():
            #    self._saveFITS(img)
            #    return self._endReadout(next_filename)

        # end readout and save
        
        try:
            manager = self.getManager()
            hostPort = manager.getHostname() + ':' + str(manager.getPort())

            tel = manager.getProxy("/Telescope/0")
            imageRequest["metadatapost"].append(hostPort+"/Telescope/0")

        except Exception:
            self.log.info("Couldn't found an telescope, WCS info will be incomplete")

        try:
            cam = manager.getProxy("/Camera/0")
            imageRequest["metadatapost"].append(hostPort+"/Camera/0")
        except Exception:
            pass # will never happen!


        imageRequest.addPostHeaders(self.getManager())

        binFactor = self._binning_factors[binning]
        scale_x = binFactor * (((180/pi) / cam["telescope_focal_length"]) * (self.getPixelSize()[0] * 0.001))
        scale_y = binFactor * (((180/pi) / cam["telescope_focal_length"]) * (self.getPixelSize()[1] * 0.001))
        
        fullsize = self.drv.readoutModes[self.ccd][0]
        
        CRPIX1 = ((int(fullsize.width/2)) - left) - 1
        CRPIX2 = ((int(fullsize.height/2)) - top) - 1
        
        img = Image.imageFromImg(img, imageRequest, [
                ('DATE-OBS',Image.formatDate(self.lastFrameStartTime),'Date exposure started'),
                ('CCD-TEMP',self.lastFrameTemp,'CCD Temperature at Exposure Start [deg. C]'),
                ("EXPTIME", float(imageRequest['exp_time']) or -1, "exposure time in seconds"),
                ('IMAGETYP', imageRequest['image_type'].strip(), 'Image type'),
                ('SHUTTER',str(imageRequest['shutter']), 'Requested shutter state'),
                ("CRPIX1", CRPIX1, "coordinate system reference pixel"),
                ("CRPIX2", CRPIX2, "coordinate system reference pixel"),
                ("CD1_1", scale_x, "transformation matrix element (1,1)"),
                ("CD1_2", 0.0, "transformation matrix element (1,2)"),
                ("CD2_1", 0.0, "transformation matrix element (2,1)"),
                ("CD2_2", scale_y, "transformation matrix element (2,2)")])
                                 
        return self._endReadout(img)

    def _endReadout(self, imageURI):
        
        self.drv.endReadout(self.ccd)
        self.readoutComplete(imageURI)
        return imageURI


    # TODO
    def _getWindowAndLine(self, img):
        shape = img.shape()
        return ()

    def _getReadoutMode(self, imageRequest):

        mode = None

        try:
            binMode = self.getBinnings()[str(imageRequest["binning"])]
            binning = imageRequest["binning"]
            mode = self.drv.readoutModes[self.ccd][binMode]
        except KeyError:
            self.log.warning("Invalid binning mode, using 1x1")
            binning = "1x1"
            mode = self.drv.readoutModes[self.ccd][0]
            
        left = 0
        top = 0
        width, height = mode.getSize()

        if imageRequest["window"] != None:
            try:
                xx, yy = imageRequest["window"].split(",")
                xx = xx.strip()
                yy = yy.strip()
                x1, x2 = xx.split(":")
                y1, y2 = yy.split(":")
                
                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)

                left = min(x1,x2) - 1
                top  = min(y1,y2) - 1
                width  = (max(x1,x2) - min(x1,x2)) + 1
                height = (max(y1,y2) - min(y1,y2)) + 1

                if left < 0 or left >= mode.width:
                    raise TypeError("Invalid subframe: left=%d, ccd width (in this binning)=%d" % (left, mode.width))

                if top < 0 or top >= mode.height:
                    raise TypeError("Invalid subframe: top=%d, ccd height (in this binning)=%d" % (top,mode.height))

                if width > mode.width:
                    raise TypeError("Invalid subframe: width=%d, ccd width (int this binning)=%d" % (width, mode.width))

                if height > mode.height:
                    raise TypeError("Invalid subframe: height=%d, ccd height (int this binning)=%d" % (height, mode.height))

            except ValueError:
                left = 0
                top = 0
                width, height = mode.getSize()
            
        return (mode, binning, top, left, width, height)
