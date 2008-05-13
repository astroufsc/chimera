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


from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.camera  import ICameraExpose, ICameraTemperature
from chimera.interfaces.camera  import Shutter, Binning, Window

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
    def expose (self, exp_time,
                frames=1, interval=0.0,
                shutter=Shutter.OPEN,
                binning=Binning._1x1,
                window=Window.FULL_FRAME,
                filename="$HOME/images/$date.fits"):

        # clear abort setting
        self.abort.clear()

        if frames <= 0:
            raise ValueError("'frames' must be > 0.")

        if interval < 0:
            raise ValueError("'interval' must be >= 0.")
        
        if exp_time < 0 or exp_time > (6*3600):
            raise ValueError("'exp_time' must be >= 0 and <= 6 h.")

        # setup window
        window = None
        if window == Window.FULL_FRAME:
            window = (0.5, 0.5, 1.0, 1.0)
        elif window == Window.TOP_HALF:
            window = (0.5, 0.75, 1.0, 0.5)
        elif window == Window.BOTTOM_HALF:
            window = (0.5, 0.25, 1.0, 0.5)
        else:
            # assume FULL_FRAME
            window = (0.5, 0.5, 1.0, 1.0)


        directory = os.path.dirname(os.path.expandvars(filename)) or os.getcwd()
        file_format, file_extension = os.path.splitext(os.path.split(filename)[1])

        file_format = file_format or "$date"

        if file_extension: file_extension=file_extension[1:] # exclude "." from extension
        file_extension = file_extension or "fits"

        # setup cam parameters
        cam_params = dict(exp_time = exp_time,
                          shutter = shutter,
                          binning = binning,
                          window_x = window[0],
                          window_y = window[1],
                          window_width = window[2],
                          window_height = window[3],
                          file_format = file_format,
                          file_extension = file_extension,
                          directory = directory,
                          save_on_temp= True)

        # config driver
        drv = self.getDriver()
        
        try:
            drv += cam_params
        except (KeyError, OptionConversionException), e:
            raise ChimeraException ("Something went wrong trying to setup camera driver parameters.")

        # ok, here we go!
        filenames = []

        try:
            for frame_num in range(frames):

                # abort set?
                if self.abort.isSet():
                    return
                
                try:
                    filename = drv.expose()

                    if filename: # can be None if exposure was aborted and not saved
                        filenames.append(filename)

                    if interval > 0 and frames > 1 and frame_num < frames:
                        time.sleep(interval)
                    
                except (ValueError, IOError):
                    raise ChimeraValueError("An error occurried while trying to setup the exposure.")

        finally:
            return tuple(filenames)

    def abortExposure (self, readout=True):
        self.abort.set() # stop expose loop
        drv = self.getDriver()
        drv += {"readout_aborted": readout}
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
