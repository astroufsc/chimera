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


from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.util.enum  import Enum

Shutter = Enum('OPEN', 'CLOSE', 'LEAVE_AS_IS')

SHUTTER_OPEN    = Shutter.OPEN
SHUTTER_CLOSE   = Shutter.CLOSE
SHUTTER_LEAVE   = Shutter.LEAVE_AS_IS

#Shutter     = {'OPEN':  SHUTTER_OPEN,
#               'CLOSE': SHUTTER_CLOSE,
#               'LEAVE': SHUTTER_LEAVE}


#Shutter = Enum ("OPEN",
#                "CLOSE",
#                "LEAVE_AS_IS")

class ICamera (Interface):
    """Base camera interface.
    """

    # config
    __config__ = {"driver" : "/FakeCamera/0",

                  "camera_model"    : "Fake camera Inc.",
                  "ccd_model"       : "KAF XYZ 10",
                  "ccd_dimension_x" : 100,  # pixel
                  "ccd_dimension_y" : 100,  # pixel
                  "ccd_pixel_size_x": 10.0, # micrometer (without binning factors)
                  "ccd_pixel_size_y": 10.0  # micrometer (without binning factors)
                  }


class ICameraExpose (ICamera):
    """Basic camera that can expose and abort exposures.
    """

    def expose (self, request=None, **kwargs):
        
        """Start an exposure based upon the specified image request or will create
        a new image request from kwargs

        @param request: ImageRequest containing details of the image to be taken
        @type  request: ImageRequest
                       
        @return: ImageURI if exposure succeeds; False otherwise
        @rtype: bool or ImageURI
        """

    def abortExposure (self, readout=True):
        """Try abort the current exposure, reading out the current frame if asked to.

        @param readout: Whether to readout the current frame after abort, otherwise the
                        current photons will be lost forever. Default is True
        @type  readout: bool

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def isExposing (self):
        """Ask if camera is exposing right now.

        @return: The currently exposing ImageRequest if the camera is exposing, False otherwise.
        @rtype: bool or chimera.controllers.imageserver.imagerequest.ImageRequest
        """
    
    def getBinnings(self):
        """Return the allowed binning settings for this camera
        
        @return: Dictionary with the keys being the English binning description (caption), and 
                 the values being a device-specific value needed to activate the described binning
        @rtype: dictionary
        """
        return {'1x1': 0}

    @event
    def exposeBegin (self, exp_time):
        """Indicates that new exposure is starting.

        When multiple frames are taken in a single shot, multiple exposeBegin events will be fired.

        @param exp_time: How long the exposure will long.
        @type  exp_time: float
        """
        
    @event
    def exposeComplete (self):
        """Indicates that new exposure frame was taken.

        When multiple frames are taken in a single shot, multiple exposeComplete events will be fired.
        """

    @event
    def readoutBegin (self, filename):
        """Indicates that new readout is starting.

        When multiple frames are taken in a single shot, multiple readoutBegin events will be fired.

        @param filename: Where this new frame was put in the filesystem.
        @type  filename: str
        """

    @event
    def readoutComplete (self, filename):
        """Indicates that a new frame was exposed and saved.

        @param filename: Where this new frame was put in the filesystem.
        @type  filename: str
        """

    @event
    def abortComplete (self):
        """Indicates that a frame exposure was aborted.
        """


class ICameraTemperature (ICamera):
    """A camera that supports temperature monitoring and control.
    """

    __config__ = {"temperature_monitor_delta": 2.0}
    

    def startCooling (self, tempC):
        """Start cooling the camera with setpoint setted to tempC.

        @param tempC: Setpoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def stopCooling (self):
        """Stop cooling the camera

        @return: True if successful, False otherwise.
        @rtype: bool
        """
    
    def setTemperature(self, tempC):
        """Set new setpoint temperature (if cooling is disabled, this will turn it on).

        @param tempC: New setpoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def getTemperature(self):
        """Get the current camera temperature.

        @return: The current camera temperature in degrees Celsius.
        @rtype: float
        """

    def getSetpoint(self):
        """Get the current camera temperature setpoint.

        @return: The current camera temperature setpoint in degrees Celsius.
        @rtype: float
        """

    @event
    def temperatureChange (self, newTempC, delta):
        """Camera temperature probe. Will be fired everytime that the camera temperature changes more than
        temperature_monitor_delta degrees Celsius.

        @param newTempC: The current camera temperature in degrees Celsius.
        @type newTempC: float

        @param delta: How much the temperature has changed in degrees Celsius.
        @type  delta: float
        """
