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


class ICamera (Interface):
    """Base camera interface.
    """

    # config
    __config__ = {"driver" : "/FakeCamera/0",

                  "camera_model"    : "Fake camera Inc.",
                  "ccd_model"       : "KAF XYZ 10",
                  "telescope_focal_length": 4000 # milimeter
                  }


class ICameraExpose (ICamera):
    """Basic camera that can expose and abort exposures.
    """

    def expose (self, request=None, **kwargs):

        """Start an exposure based upon the specified image request or will create
        a new image request from kwargs

        @param request: ImageRequest containing details of the image to be taken
        @type  request: ImageRequest

        @return: L{Image} proxy if exposure succeeds; False otherwise
        @rtype: bool or L{Proxy}
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
    def readoutComplete (self, filename):
        """Indicates that a new frame was exposed and saved.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def abortComplete (self):
        """Indicates that a frame exposure was aborted.
        """


class ICameraTemperature (ICamera):
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

    def setTemperature(self, tempC):
        """Set new SetPoint temperature (if cooling is disabled, this will turn it on).

        @param tempC: New SetPoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successful, False otherwise.
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

class ICameraInformation (ICamera):

    # for getCCDs, getBinnings and getADCs, the driver should returns a
    # list of Human readable strings, which could be later passed as a
    # ImageRequest and be recognized by the driver. Those strings can
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

    def supports(self, feature=None):
        pass

