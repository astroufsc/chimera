import logging

from FLI.device import USBDevice
from FLI.camera import USBCamera
from FLI.filter_wheel import USBFilterWheel

from chimera.interfaces.camera import (CCD, CameraFeature, Bitpix)
from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.instruments.camera import CameraBase

from chimera.instruments.fli import FLIDrv

log = logging.getLogger(__name__)


class FLI():
    # Some of the config values were taken from the specs for the cam & CCD.
    __config__ = {"device": "USB",
                  "ccd": CCD.IMAGING,
                  "temp_delta": 2.0,

                  "ccd_saturation_level": 100000,

                  "camera_model": "Finger Lakes Instrumentation PL4240",
                  "ccd_model": "E2V CCD42-40",
                  "telescope_focal_length": 4000  # milimeter
                  }

    def __init__(self):
        CameraBase.__init__(self)
        #FilterWheelBase.__init__(self)
        self.mode = 0
        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: True,
                          CameraFeature.PROGRAMMABLE_FAN: False,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

    def __start__(self):
        # Find devices attached to the USB bus. Supposedly this call
        # returns a list...of USBDevice objects. How to recognize them:
        # by dev_name/flidev_t?
        self._devs = USBDevice.find_devices()
        # TODO: get the devices, instantiate them

        # This will provide the following dict pairs:
        # 'serial_number', 'hardware_rev', 'firmware_rev', 'pixel_size',
        # 'array_area', 'visible_area'.

        #self.info = self._devs[???].get_info()

        # Getting this here guarantees info is available no matter
        # in what order the methods are invoked...
        #self.width, self.height, self.imgsz = self._devs[camera].get_image_size()
        self.pixelWidth = 13.5  # µm, from specs.
        self.pixelHeight = 13.5  # µm

    # From ReadoutMode()
    def getSize(self):
        """
        Gets the current CCD size, accounting for binning
        factors.
        """
        return (self.width, self.height)

    def getWindow(self):
        return [0, 0, self.width, self.height]

    def getPixelSize(self):
        return self.info['pixel_size']

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

    # From CameraTemperature()
    def startCooling(self, tempC):
        """
        Start cooling the camera with SetPoint setted to tempC.

        @param tempC: SetPoint temperature in degrees Celsius.
        @type  tempC: float or int

        @return: True if successful, False otherwise.
        @rtype: bool
        """
        raise NotImplementedError()

    def stopCooling(self):
        """
        Stop cooling the camera

        @return: True if successful, False otherwise.
        @rtype: bool
        """
        raise NotImplementedError()

    def isCooling(self):
        """
        Returns whether the camera is currently cooling.

        @return: True if cooling, False otherwise.
        @rtype: bool
        """
        raise NotImplementedError()

    def getTemperature(self):
        """
        Get the current camera temperature.

        @return: The current camera temperature in degrees Celsius.
        @rtype: float
        """
        #return self._devs[camera].get_temperature()

    def getSetPoint(self):
        """
        Get the current camera temperature SetPoint.

        @return: The current camera temperature SetPoint in degrees Celsius.
        @rtype: float
        """
        raise NotImplementedError()

    def startFan(self, rate=None):
        pass

    def stopFan(self):
        pass

    def isFanning(self):
        """
        Find out by means of querying the power consumption of the
        camera's cooler.
        NOTE: this is flagged as an "undocumented API function"!
        """
        # We might need this info one day...
        # watts = self._devs[camera].get_cooler_power()
        # if watts == 0:
        #     return False
        # else:
        #     return True

    # From CameraInformation
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

    def getOverscanSize(self):
        pass

    def getReadoutModes(self):
        """Get readout modes supported by this camera.
        The return value would have the following format:
         {ccd1: {mode1: ReadoutMode(), mode2: ReadoutMode2()},
          ccd2: {mode1: ReadoutMode(), mode2: ReadoutMode2()}}
        """

    # From CameraExpose!
    def expose(self, request=None, **kwargs):
        """
        Start an exposure based upon the specified image request or
        create a new image request from kwargs
        """

    def abortExposure(self, readout=True):
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

    def isExposing(self):
        """
        Ask if camera is exposing right now.(where exposing
        includes both integration time and readout).

        @return: The currently exposing ImageRequest if the camera is
                 exposing, False otherwise.

        @rtype: bool or L{ImageRequest}
        """

    @event
    def exposeBegin(self, request):
        """
        Indicates that new exposure is starting.

        When multiple frames are taken in a single shot, multiple
        exposeBegin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def exposeComplete(self, request, status):
        """
        Indicates that new exposure frame was taken.

        When multiple frames are taken in a single shot, multiple
        exposeComplete events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}

        @param status: The status of the current expose.
        @type  status: L{CameraStatus}
        """

    @event
    def readoutBegin(self, request):
        """
        Indicates that new readout is starting.

        When multiple frames are taken in a single shot, multiple
        readoutBegin events will be fired.

        @param request: The image request.
        @type  request: L{ImageRequest}
        """

    @event
    def readoutComplete(self, proxy, status):
        """Indicates that a new frame was exposed and saved.

        @param request: The just taken Image (as a Proxy) or None is status=[ERROR or ABORTED]..
        @type  request: L{Proxy} or None

        @param status: current exposure status
        @type  status: L{CameraStatus}
        """

    # Filter wheel
    @lock
    def setFilter(self, filter):
        #self._devs[filterwheel].set_filter_pos(filter)
        pass

    def getFilter(self):
        #return self._devs[filterwheel].get_filter_pos()
        pass

    def getFilters(self):
        raise NotImplementedError()

    # def _getFilterName(self, index):
    #     try:
    #         return self.getFilters()[index]
    #     except (ValueError, TypeError):
    #         raise InvalidFilterPositionException(
    #             "Unknown filter (%s)." % str(index))


    # Shutter
    def getMetadata(self, request):
        return [('FWHEEL', str(self['filter_wheel_model']), 'FilterWheel Model'),
                ('FILTER', str(self.getFilter()),
                 'Filter used for this observation')]
