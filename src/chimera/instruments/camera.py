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


import threading
import os
import time
import Pyro.util

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.camera import ICameraExpose, ICameraTemperature, SHUTTER_LEAVE

from chimera.controllers.imageserver.imagerequest import ImageRequest

from chimera.core.exceptions import OptionConversionException
from chimera.core.exceptions import ChimeraValueError
from chimera.core.exceptions import ChimeraException

from chimera.core.lock import lock


class Camera (ChimeraObject, ICameraExpose, ICameraTemperature):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.abort = threading.Event()
        self.abort.clear()

    def getDriver(self):
        """
        Get a Proxy to the instrument driver. This function is necessary '
        cause Proxies cannot be shared among different threads.
        So, every time you need a driver Proxy you need to call this to
        get a Proxy to the current thread.
        """
        return self.getManager().getProxy(self['driver'], lazy=True)        
        
    def __start__ (self):

        drv = self.getDriver()

        # connect callbacks to driver events
        drv.exposeBegin       += self.getProxy()._exposeBeginDrvClbk        
        drv.exposeComplete    += self.getProxy()._exposeCompleteDrvClbk
        drv.readoutBegin      += self.getProxy()._readoutBeginDrvClbk
        drv.readoutComplete   += self.getProxy()._readoutCompleteDrvClbk        
        drv.abortComplete     += self.getProxy()._abortDrvClbk
        drv.temperatureChange += self.getProxy()._tempChangeDrvClbk

        return True

    def __stop__ (self):
        
        if self.isExposing():
            self.abortExposure(False)
            while self.isExposing():
                time.sleep(1)
        
        # disconnect our callbacks
        drv = self.getDriver()

        drv.exposeBegin       -= self.getProxy()._exposeBeginDrvClbk        
        drv.exposeComplete    -= self.getProxy()._exposeCompleteDrvClbk
        drv.readoutBegin      -= self.getProxy()._readoutBeginDrvClbk
        drv.readoutComplete   -= self.getProxy()._readoutCompleteDrvClbk        
        drv.abortComplete     -= self.getProxy()._abortDrvClbk
        drv.temperatureChange -= self.getProxy()._tempChangeDrvClbk

    def _exposeBeginDrvClbk (self, exp_time):
        self.exposeBegin(exp_time)
    
    def _exposeCompleteDrvClbk (self):
        self.exposeComplete()

    def _readoutBeginDrvClbk (self, filename):
        self.readoutBegin(filename)
    
    def _readoutCompleteDrvClbk (self, filename):
        self.readoutComplete(filename)

    def _abortDrvClbk (self):
        self.abortComplete()
    
    def _tempChangeDrvClbk (self, temp, delta):
        self.temperatureChange(temp, delta)

    @lock
    def expose (self, *args, **kwargs):
        
        if len(args) > 0:
            if isinstance(args[0], ImageRequest):
                imageRequest = args[0]
            else:
                imageRequest = ImageRequest(kwargs)
                imageRequest += kwargs
        else:
            imageRequest = ImageRequest()
        
        frames = imageRequest['frames']
        interval = imageRequest['interval']
        if frames == 1:
            interval = 0.0

        # clear abort setting
        self.abort.clear()

        # config driver
        drv = self.getDriver()
        
        imageURIs = []
        self.log.debug('Looping through ' + str(frames) + ' frames...')
        for frame_num in range(frames):
            
            if self.abort.isSet():
                return imageURIs
            
            try:
                imageRequest.addPreHeaders(self.getManager())
                imageURI = None
                try:
                    imageURI = drv.expose(imageRequest)
                    self.log.debug('Got back imageURI = ' + str(imageURI) + '[' + str(frame_num) + '/' + str(frames) + ']')
                    self.log.info(str(imageRequest) + ': [' + str(frame_num) + '/' + str(frames) + '] done')
                except Exception, e:
                    print ''.join(Pyro.util.getPyroTraceback(e))
                
                if imageURI:
                    
                    imageURIs.append(imageURI)
                    del imageURI
                
                if interval > 0 and frame_num < frames:
                    time.sleep(interval)
            except ValueError:
                raise ChimeraValueError('An error occurred while trying to take the exposure.')
        
        return tuple(imageURIs)
                
        
    def abortExposure (self, readout=True):
        drv = self.getDriver()
        drv.abortExposure()

        return True
    
    def isExposing (self):
        drv = self.getDriver()
        return drv.isExposing()

    @lock
    def startCooling (self, tempC):
        drv = self.getDriver()
        
        drv += {"temp_setpoint": tempC}

        drv.startCooling()
        return True

    @lock
    def stopCooling (self):
        drv = self.getDriver()
        drv.stopCooling()
        return True

    def isCooling (self):
        drv = self.getDriver()
        return drv.isCooling()

    def getTemperature(self):
        drv = self.getDriver()
        return drv.getTemperature()

    def getSetpoint(self):
        drv = self.getDriver()
        return drv.getSetpoint()
    
    def getMetadata(self):
        return [
                ('INSTRUME', str(self['camera_model']), 'Camera Model'),
                ('CCD',      str(self['ccd_model']), 'CCD Model'),
                ('CCD_DIMX', self['ccd_dimension_x'], 'CCD X Dimension Size'),
                ('CCD_DIMY', self['ccd_dimension_y'], 'CCD Y Dimension Size'),
                ('CCDPXSZX', self['ccd_pixel_size_x'], 'CCD X Pixel Size [microns]'),
                ('CCDPXSZY', self['ccd_pixel_size_y'], 'CCD Y Pixel Size [micrpns]'),
                ] + self.getDriver().getMetadata()
