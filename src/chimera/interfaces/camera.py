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


Shutter = Enum ("OPEN",
                "CLOSE",
                "LEAVE_AS_IS")

# _ needed because identifier cannot begin with a number
Binning = Enum ("_1x1",
                "_2x2",
                "_3x3",
                "_9x9",
                "_1x2",
                "_1x3",
                "_1x9",
                "_2x1",
                "_3x1",
                "_9x1")

Window = Enum ("FULL_FRAME",
               "TOP_HALF",
               "BOTTOM_HALF")


class ICamera (Interface):
    """Base camera interface.
    """

    # config
    __config__ = {"driver" : "/Fake/camera",

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

    __config__ = {"date_format": "dd-mm-yyyy-hh-mm-ss"}


    def expose (self,
                exp_time,
                frames=1, interval=0.0,
                shutter=Shutter.OPEN,
                binning=Binning._1x1,
                window=Window.FULL_FRAME,
                filename="$date.fits"):
        
        """Start an exposure of exp_time seconds of integration time,
        using the parameters given.

        @param exp_time: Integration time in seconds.
        @type  exp_time: float or int

        @param frames: Number of frames to take using this exposure frame. Default 1 (single shot).
        @type  frames: int
        
        @param interval: Number of seconds to wait between each frame exposure. Default 0.
        @type  interval: float or int

        @param shutter: The shutter state desired for this exposure. See L{Shutter} for values. Default is Shutter.OPEN.
        @type  shutter: Shutter

        @param binning: The desired binning. See L{Binning} for values. Default is Binning._1x1.
                        You can also pass a tuple of (x,y) binning if Binning doesn't have your desired one.
        
        @type  binning: Binning or tuple
        
        @param window: The desired CCD window to expose in a tuple like (x_center, y_center, width, height) in pixels or a Window constant.
                       Default is Window.FULL_FRAME. If any tuple value was given as float, they will be interpreted as a percentage of the
                       maximum allowed value. So, a full frame would be like (0.5, 0.5, 1.0, 1.0).
        
        @type  window: tuple

        @param filename: The filename where the frames will saved. Directory is specified here also,
                         like '/directory/image-filename.fits'. The filename can have environment variables and
                         keywords as defined below:

                          - $date: current date in the format define in date_format configuration
                       
        @return: The filenames (tuple if more than one) of the frames taken, empty tuple if fail.
        @rtype: tuple
        """

    def abortExposure (self, readout=True):
        """Try abort the current exposure, reading out the current frame if asked to.

        @param readout: Wether to readout the current frame after abort, otherwise the
                        current photons will be lost forever. Default is True
        @type  readout: bool

        @return: True if successfull, False otherwise.
        @rtype: bool
        """

    def isExposing (self):
        """Ask if camera is exposing right now.

        @return: True if the camera is exposing, False otherwise.
        @rtype: bool
        """


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

        @return: True if successfull, False otherwise.
        @rtype: bool
        """

    def stopCooling (self):
        """Stop cooling the camera

        @return: True if successfull, False otherwise.
        @rtype: bool
        """
    
    def setTemperature(self, tempC):
        """Set new setpoint temperature (if cooling is disabled, this will turn it on).

        @param tempC: New setpoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successfull, False otherwise.
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
        """Camera temperature probe. Will be fired eveytime that the camera temperatude changes more than
        temperature_monitor_delta degrees Celsius.

        @param newTempC: The current camera temperature in degrees Celsius.
        @type newTempC: float

        @param delta: How much the temperatude has changed in degrees Celsius.
        @type  delta: float
        """
