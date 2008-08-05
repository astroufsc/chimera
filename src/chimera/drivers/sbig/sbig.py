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
from math import pi
import numpy as N
        
from sbigdrv import *

from chimera.core.chimeraobject            import ChimeraObject
from chimera.interfaces.cameradriver       import ICameraDriver, CCD, Device, Bitpix
from chimera.interfaces.camera             import Shutter#, Binning 
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

    def __start__ (self):

        #if self['ccd'] == CCD.IMAGING:
        self.ccd = SBIGDrv.imaging
#        else:
#            self.ccd = SBIGDrv.tracking
#           
        if self['device'] == Device.USB:
            self.dev = SBIGDrv.usb
        else:
            self.dev = SBIGDrv.lpt1

        #self["bitpix"] = Bitpix.uint16

        #self["bitpix"] = Bitpix.uint16
                        
	self.open(self.dev)

	# make sure filter wheel is in the right position
	self.setFilter(0)

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
    def expose(self, imageRequest):

        self.term.clear()

        if self._expose(imageRequest):
            return self._readout(imageRequest, aborted=False)
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
        
    def _expose(self, imageRequest):
        
        shutterRequest = imageRequest['shutter'][1]
        
        #TODO: Support CCD Selection
        #ccdRequest = imageRequest['ccd'][1]

        if shutterRequest == Shutter.OPEN:
            shutter = SBIGDrv.openShutter
        elif shutterRequest == Shutter.CLOSE:
            shutter = SBIGDrv.closeShutter
        elif shutterRequest == Shutter.LEAVE_AS_IS:
            shutter = SBIGDrv.leaveShutter
        else:
            #raise ValueError("Incorrect shutter option (%s). Leaving shutter intact" % shutterRequest)
            self.log.warning("Incorrect shutter option (%s). Leaving shutter intact" % shutterRequest)
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

        # fire exposeComplete event
        self.exposeComplete()

        return True

    def _readout(self, imageRequest, aborted=False):

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

#        try:
#            next_filename = ImageSave.save(None,
#                                           self["directory"],
#                                           self["file_format"],
#                                           self["file_extension"],
#                                           self["date_format"],
#                                           self.lastFrameStartTime,
#                                           self["exp_time"],
#                                           self["bitpix"],
#                                           self["save_on_temp"],
#                                           dry=True)
#        except Exception, e:
#            print e

        self.readoutBegin(imageRequest)

        self.drv.startReadout(self.ccd, 0)
        
        for line in range(readoutMode.height):
	
            img[line] = self.drv.readoutLine(self.ccd, 0)

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

        scale_x = ((180/pi) / cam["telescope_focal_length"]) * (cam["ccd_pixel_size_x"] * 0.001)
        scale_y = ((180/pi) / cam["telescope_focal_length"]) * (cam["ccd_pixel_size_y"] * 0.001)
        
        img = Image.imageFromImg(img, imageRequest, [
                ("EXPTIME", float(imageRequest['exp_time']) or -1, "exposure time in seconds"),
                ('IMAGETYP', imageRequest['image_type'].upper().strip(), 'Image type'),
                ('DATE-OBS',Image.formatDate(self.lastFrameStartTime),'Date exposure started'),
                ('CCD-TEMP',self.lastFrameTemp,'CCD Temperature at Exposure Start [deg. C]'),
                ('XBINNING',1,'Readout CCD Binning (x-axis)'),
                ('YBINNING',1,'Readout CCD Binning (y-axis)'),
                ('XWIN_LFT',0,'Readout window x left position'),
                ('XWIN_SZ',readoutMode.width,'Readout window width'),
                ('YWIN_TOP',0,'Readout window y top position'),
                ('YWIN_SZ',readoutMode.height,'Readout window height'),
                ('IMAGETYP',imageRequest['image_type'],'Image type'),
                ('SHUTTER',str(imageRequest['shutter'][1]), 'Requested shutter state'),
                ("CRPIX1", int(readoutMode.width/2.0), "coordinate system reference pixel"),
                ("CRPIX2", int(readoutMode.height/2.0), "coordinate system reference pixel"),
                ("CD1_1", scale_x, "transformation matrix element (1,1)"),
                ("CD1_2", 0.0, "transformation matrix element (1,2)"),
                ("CD2_1", 0.0, "transformation matrix element (2,1)"),
                ("CD2_2", scale_y, "transformation matrix element (2,2)")])

        return self._endReadout(img)

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

#    def _saveFITS(self, img):
#
#        try:
#            self.lastFrameFilename = ImageSave.save(img,
#                                                    self["directory"],
#                                                    self["file_format"],
#                                                    self["file_extension"],
#                                                    self["date_format"],
#                                                    self.lastFrameStartTime,
#                                                    self["exp_time"],
#                                                    self["bitpix"],
#                                                    self["save_on_temp"])
#        except Exception, e:
#            print e
            
    def _endReadout(self, imageURI):
        
        self.drv.endReadout(self.ccd)
        self.readoutComplete(imageURI)
        return imageURI
