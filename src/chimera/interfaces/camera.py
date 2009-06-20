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
from chimera.core.exceptions import ChimeraException

Shutter = Enum('OPEN', 'CLOSE', 'LEAVE_AS_IS')
Bitpix  = Enum("char8", "uint16", "int16", "int32", "int64", "float32", "float64")
CCD     = Enum("IMAGING", "TRACKING")

# Special features parameters can be passed as ImageRequest
# parameters. The Camera.supports(feature) method can be used
# to ask if the current camera support a given feature (useful for
# interfaces, to decides when to display options to the user).

CameraFeature = Enum("TEMPERATURE_CONTROL",
                     "PROGRAMMABLE_GAIN",
                     "PROGRAMMABLE_OVERSCAN",
                     "PROGRAMMABLE_FAN",
                     "PROGRAMMABLE_LEDS",
                     "PROGRAMMABLE_BIAS_LEVEL")


class ReadoutMode(object):
    """
    Store basic geometry for a given readout mode. Implementer should
    provide an constuctor from a modeString (some instrument specific
    internal value).

    pixelWidth and pixelHeight should provides the virtual size of a
    pixel after any on-chip sum.

    gain is in e-/ADU. All others, except mode (which is an internal
    value) are in pixel.
    """

    mode = 0
    gain = 0.0
    width = 0
    height = 0
    pixelWidth = 0.0
    pixelHeight = 0.0

    def __init__(self, modeString=""):
        pass

    def getSize(self):
        return (self.width, self.height)

    def getWindow(self):
        return [0, 0, self.width, self.height]

    def getPixelSize(self):
        return (self.pixelWidth, self.pixelHeight)

    def getLine(self):
        return [0, self.width]

    def __str__(self):
        s = "mode: %d: \n\tgain: %.2f\n\tWxH: [%d,%d]" \
            "\n\tpix WxH: [%.2f, %.2f]" % (self.mode,
                                           self.gain,
                                           self.width, self.height,
                                           self.pixelWidth, self.pixelHeight)
        return s

    def __repr__(self):
        return self.__str__()


class InvalidReadoutMode (ChimeraException):
    pass


class Camera (Interface):
    """Base camera interface.
    """

    # config
    __config__ = {"device"     : "USB",
                  "ccd"        : CCD.IMAGING,
                  "temp_delta" : 2.0,

                  "camera_model"    : "Fake camera Inc.",
                  "ccd_model"       : "KAF XYZ 10",
                  "telescope_focal_length": 4000 # milimeter
                  }


class CameraExpose (Camera):
    """Basic camera that can expose and abort exposures.
    """

    def expose (self, request=None, **kwargs):

        """Start an exposure based upon the specified image request or
        will create a new image request from kwargs

        @param request: ImageRequest containing details of the image to be taken
        @type  request: ImageRequest

        @return: L{Image} proxy if exposure succeeds; False otherwise
        @rtype: bool or L{Proxy}
        """

    def abortExposure (self, readout=True):
        """Try abort the current exposure, reading out the current
        frame if asked to.

        @param readout: Whether to readout the current frame after
                        abort, otherwise the current photons will be
                        lost forever. Default is True @type readout:
                        bool

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def isExposing (self):
        """Ask if camera is exposing right now.

        @return: The currently exposing ImageRequest if the camera is
        exposing, False otherwise.  

        @rtype: bool or L{ImageRequest}
        """

    @event
    def exposeBegin (self, request):
        """Indicates that new exposure is starting.

        When multiple frames are taken in a single shot, multiple
        exposeBegin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def exposeComplete (self, request):
        """Indicates that new exposure frame was taken.

        When multiple frames are taken in a single shot, multiple
        exposeComplete events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def readoutBegin (self, request):
        """Indicates that new readout is starting.

        When multiple frames are taken in a single shot, multiple
        readoutBegin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def readoutComplete (self, proxy):
        """Indicates that a new frame was exposed and saved.

        @param request: The just taken Image (as a Proxy).
        @type  request: L{Proxy}
        """

    @event
    def abortComplete (self):
        """Indicates that a frame exposure was aborted.
        """


class CameraTemperature (Camera):
    """A camera that supports temperature monitoring and control.
    """


    def startCooling (self, tempC):
        """Start cooling the camera with SetPoint setted to tempC.

        @param tempC: SetPoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def stopCooling (self):
        """Stop cooling the camera

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def isCooling (self):
        """Returns whether the camera is currently cooling.

        @return: True if cooling, False otherwise.
        @rtype: bool
        """

    def getTemperature(self):
        """Get the current camera temperature.

        @return: The current camera temperature in degrees Celsius.
        @rtype: float
        """

    def getSetPoint(self):
        """Get the current camera temperature SetPoint.

        @return: The current camera temperature SetPoint in degrees Celsius.
        @rtype: float
        """

    def startFan(self, rate=None):
        pass

    def stopFan(self):
        pass

    def isFanning(self):
        pass


    @event
    def temperatureChange (self, newTempC, delta):
        """Camera temperature probe. Will be fired everytime that the camera
        temperature changes more than temperature_monitor_delta
        degrees Celsius.

        @param newTempC: The current camera temperature in degrees Celsius.
        @type newTempC: float

        @param delta: How much the temperature has changed in degrees Celsius.
        @type  delta: float
        """

class CameraInformation (Camera):

    # for getCCDs, getBinnings and getADCs, the instrument should return a
    # hash with keys as Human readable strings, which could be later passed as a
    # ImageRequest and be recognized by the intrument. Those strings can
    # be use as key to an internal hashmap.
    # example:
    # ADCs = {'12 bits': SomeInternalValueWhichMapsTo12BitsADC,
    #         '16 bits': SomeInternalValueWhichMapsTo16BitsADC}


    def getCCDs(self):
        pass

    def getCurrentCCD(self):
        pass

    def getBinnings(self):
        pass

    def getADCs(self):
        pass

    def getPhysicalSize(self):
        pass

    def getPixelSize(self):
        pass

    def getOverscanSize(self):
        pass

    def getReadoutModes(self):
        """Get readout modes supported by this camera.
        The return value would have the following format:
         {ccd1: {mode1: ReadoutMode(), mode2: ReadoutMode2()},
          ccd2: {mode1: ReadoutMode(), mode2: ReadoutMode2()}}
        """

    #
    # special features support
    #
    
    def supports(self, feature=None):
        pass

