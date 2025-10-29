# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class Shutter(Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    LEAVE_AS_IS = "LEAVE_AS_IS"


class Bitpix(Enum):
    char8 = "char8"
    uint16 = "uint16"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    float32 = "float32"
    float64 = "float64"


class CCD(Enum):
    IMAGING = "IMAGING"
    TRACKING = "TRACKING"


# Special features parameters can be passed as ImageRequest
# parameters. The Camera.supports(feature) method can be used
# to ask if the current camera support a given feature (useful for
# interfaces, to decide when to display options to the user).


class CameraFeature(Enum):
    TEMPERATURE_CONTROL = "TEMPERATURE_CONTROL"
    PROGRAMMABLE_GAIN = "PROGRAMMABLE_GAIN"
    PROGRAMMABLE_OVERSCAN = "PROGRAMMABLE_OVERSCAN"
    PROGRAMMABLE_FAN = "PROGRAMMABLE_FAN"
    PROGRAMMABLE_LEDS = "PROGRAMMABLE_LEDS"
    PROGRAMMABLE_BIAS_LEVEL = "PROGRAMMABLE_BIAS_LEVEL"


class CameraStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class ReadoutMode:
    """
    Store basic geometry for a given readout mode. Implementer should
    provide an constuctor from a mode_string (some instrument specific
    internal value).

    pixel_width and pixel_height should provide the virtual size of a
    pixel after any on-chip sum.

    gain is in e-/ADU. All others, except mode (which is an internal
    value) are in pixels.
    """

    mode = 0
    gain = 0.0
    width = 0
    height = 0
    pixel_width = 0.0
    pixel_height = 0.0

    def __init__(self, mode_string=""):
        pass

    def get_size(self):
        return (self.width, self.height)

    def get_window(self):
        return [0, 0, self.width, self.height]

    def get_pixel_size(self):
        return (self.pixel_width, self.pixel_height)

    def get_line(self):
        return [0, self.width]

    def __str__(self):
        return (
            f"mode: {self.mode}: \n\tgain: {self.gain:.2f}\n\tWxH: [{self.width},{self.height}]"
            f"\n\tpix WxH: [{self.pixel_width:.2f}, {self.pixel_height:.2f}]"
        )

    def __repr__(self):
        return self.__str__()


class InvalidReadoutMode(ChimeraException):
    pass


class Camera(Interface):
    """
    Base camera interface.
    """

    __config__ = {
        "device": "Unknown",  # Bus address identifier for this camera. E.g. USB, LPT1, ...
        "ccd": CCD.IMAGING,  # CCD to be used when multiple ccd camera. IMAGING or TRACKING.
        "camera_model": "Unknown",  # Camera model string. To be used by metadata purposes
        "ccd_model": "Unknown",  # CCD model string. To be used by metadata purposes
        "ccd_saturation_level": None,  # CCD level at which arises saturation (in ADUs).
        # Needed by SExtractor when doing auto-focus, autoguiding...
        # WCS configuration parameters  #
        "telescope_focal_length": None,  # Telescope focal length (in millimeters)
        "rotation": 0.0,  # Angle between the North and the second axis of the image counted
        # positive to the East (in degrees)
    }


class CameraExpose(Camera):
    """
    Basic camera that can expose and abort exposures.
    """

    def expose(self, request=None, **kwargs):
        """
        Start an exposure based upon the specified image request or
        will create a new image request from kwargs

        @param request: ImageRequest containing details of the image to be taken
        @type  request: ImageRequest

        @return: tuple of L{Image} proxies (empty if no one was taken)
        @rtype: tuple(L{Proxy})
        """

    def abort_exposure(self, readout=True):
        """
        Try abort the current exposure, reading out the current
        frame if asked to.

        @param readout: Whether to readout the current frame after
                        abort, otherwise the current photons will be
                        lost forever. Default is True
        @type readout: bool

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def is_exposing(self):
        """
        Ask if camera is exposing right now.(where exposing
        includes both integration time and readout).

        @return: The currently exposing ImageRequest if the camera is
        exposing, False otherwise.

        @rtype: bool or L{ImageRequest}
        """

    @event
    def expose_begin(self, request):
        """
        Indicates that new exposure is starting.

        When multiple frames are taken in a single shot, multiple
        expose_begin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def expose_complete(self, request, status):
        """
        Indicates that new exposure frame was taken.

        When multiple frames are taken in a single shot, multiple
        expose_complete events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}

        @param status: The status of the current expose.
        @type  status: L{CameraStatus}
        """

    @event
    def readout_begin(self, request):
        """
        Indicates that new readout is starting.

        When multiple frames are taken in a single shot, multiple
        readout_begin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def readout_complete(self, proxy, status):
        """
        Indicates that new readout is complete.

        @param request: The just taken Image (as a Proxy) or None is status=[ERROR or ABORTED]..
        @type  request: L{Proxy} or None

        @param status: The status of the current expose.
        @type  status: L{CameraStatus}
        """


class CameraTemperature(Camera):
    """
    A camera that supports temperature monitoring and control.
    """

    def start_cooling(self, temp_c):
        """
        Start cooling the camera with SetPoint setted to temp_c.

        @param temp_c: SetPoint temperature in degrees Celsius.
        @type  temp_c: float or int

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def stop_cooling(self):
        """
        Stop cooling the camera

        @return: True if successful, False otherwise.
        @rtype: bool
        """

    def is_cooling(self):
        """
        Returns whether the camera is currently cooling.

        @return: True if cooling, False otherwise.
        @rtype: bool
        """

    def get_temperature(self):
        """
        Get the current camera temperature.

        @return: The current camera temperature in degrees Celsius.
        @rtype: float
        """

    def get_set_point(self):
        """
        Get the current camera temperature SetPoint.

        @return: The current camera temperature SetPoint in degrees Celsius.
        @rtype: float
        """

    def start_fan(self, rate=None):
        pass

    def stop_fan(self):
        pass

    def is_fanning(self):
        pass

    @event
    def temperature_change(self, new_temp_c, delta):
        """
        Camera temperature probe. Will be fired everytime that the camera
        temperature changes more than temperature_monitor_delta
        degrees Celsius.

        @param new_temp_c: The current camera temperature in degrees Celsius.
        @type new_temp_c: float

        @param delta: How much the temperature has changed in degrees Celsius.
        @type  delta: float
        """


class CameraInformation(Camera):

    # for get_ccds, get_binnings and get_adcs, the instrument should return a
    # hash with keys as Human readable strings, which could be later passed as a
    # ImageRequest and be recognized by the intrument. Those strings can
    # be use as key to an internal hashmap.
    # example:
    # ADCs = {'12 bits': SomeInternalValueWhichMapsTo12BitsADC,
    #         '16 bits': SomeInternalValueWhichMapsTo16BitsADC}

    def get_ccds(self):
        pass

    def get_current_ccd(self):
        pass

    def get_binnings(self):
        pass

    def get_adcs(self):
        pass

    def get_physical_size(self):
        pass

    def get_pixel_size(self):
        pass

    def get_overscan_size(self):
        pass

    def get_readout_modes(self):
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
