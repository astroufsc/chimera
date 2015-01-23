import logging

#from FLI.device import USBDevice
from chimera.instruments.fli.flidrv.camera import USBCamera
#from FLI.filter_wheel import USBFilterWheel

from chimera.instruments.camera import CameraBase

from chimera.interfaces.camera import (CCD, CameraFeature)


log = logging.getLogger(__name__)


class FLI(CameraBase):
    """
    .. class:: FLI(CameraBase)

        High level driver for Finger Lakes instruments cameras.
        Uses the python fli bindings to the FLI provided library.
    """

    # Some of the config values were taken from the specs for the cam & CCD.
    __config__ = {"device": "USB",
                  "ccd": CCD.IMAGING,
                  "temp_delta": 2.0,
                  "ccd_saturation_level": 100000,
                  "camera_model": "Finger Lakes Instrumentation PL4240",
                  "ccd_model": "E2V CCD42-40",
                  "telescope_focal_length": 80000  # milimeter
                  }

    def __init__(self):
        CameraBase.__init__(self)
        # FilterWheelBase.__init__(self)

        self.mode = 0
        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: True,
                          CameraFeature.PROGRAMMABLE_FAN: False,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

        # Kludge: this is a camera class, let's assume we're talking to a
        # camera!
        self._cams = USBCamera.find_devices()
        # While we're at it, let's assume there's only one camera on the
        # USB bus...
        self.thecam = self._cams[0]
        # This will provide the following dict pairs:
        # 'serial_number', 'hardware_rev', 'firmware_rev', 'pixel_size',
        # 'array_area', 'visible_area'.
        self.info = self.thecam.get_info()
        # Getting this here guarantees info is available no matter
        # in what order the methods are invoked...
        self.width, self.height, self.imgsz = self.thecam.get_image_size()
        self.pixelWidth = 13.5  # µm, from specs.
        self.pixelHeight = 13.5  # µm
        log.info('Camera: %s', self.thecam.info)

    def getSize(self):
        """
        .. method:: getSize()

            Gets the current CCD size, accounting for binning
            factors.

            :return: set with values.
            :rtype: int
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

    def startCooling(self, tempC):
        """
        .. method:: startCooling(tempC)

            Start cooling the camera with SetPoint set to tempC.

            :param int tempC: SetPoint temperature in degrees Celsius.

            :return: True if successful, False otherwise.
            :rtype: bool
        """
        raise NotImplementedError()

    def stopCooling(self):
        """
        .. method:: stopCooling()

            Stop cooling the camera

            :return: True if successful, False otherwise.
            :rtype: bool
        """
        raise NotImplementedError()

    def isCooling(self):
        """
        .. method:: isCooling()

            Returns whether the camera is currently cooling.

            :return: True if cooling, False otherwise.
            :rtype: bool
        """
        raise NotImplementedError()

    def getTemperature(self):
        """
        .. method:: getTemperature()

            Get the current camera temperature.

            :return: The current camera temperature in degrees Celsius.
            :rtype: float
        """
        return self.thecam.get_temperature()

    def getSetPoint(self):
        """
        .. method:: getSetPoint()

            Get the current camera temperature SetPoint.

            :return: The current camera temperature SetPoint in degrees Celsius.
            :rtype: float
        """
        raise NotImplementedError()

    def startFan(self, rate=None):
        raise NotImplementedError()

    def stopFan(self):
        raise NotImplementedError()

    def isFanning(self):
        """
        .. method:: isFanning()

            Find out by means of querying the power consumption of the
            camera's cooler.

        .. note:: this is flagged as an "undocumented API function"!
        """
        # We might need this info one day...
        watts = self.thecam.get_cooler_power()
        if watts == 0:
            return False
        else:
            return True

    def getCCDs(self):
        raise NotImplementedError()

    def getCurrentCCD(self):
        raise NotImplementedError()

    def getBinnings(self):
        raise NotImplementedError()

    def getADCs(self):
        raise NotImplementedError()

    def getPhysicalSize(self):
        raise NotImplementedError()

    def getOverscanSize(self):
        raise NotImplementedError()

    def getReadoutModes(self):
        """
        .. method:: getReadoutModes()

            Get readout modes supported by this camera.
            The return value would have the following format:
            {ccd1: {mode1: ReadoutMode(), mode2: ReadoutMode2()},
            ccd2: {mode1: ReadoutMode(), mode2: ReadoutMode2()}}

            :return: dict of dicts describing per ccd modes.
        """
        raise NotImplementedError()

    def expose(self, request=None, **kwargs):
        """
        .. method:: expose(request=None, **kwargs)

            Start an exposure based upon the specified image request or
            create a new image request from kwargs

            :keyword request: ImageRequest object
            :type request: ImageRequest or None

        """
        # NOTE: AFAIK, there is no way an ImageRequest kw will be left
        # with no value: if no ImageRequest is passed, any value not
        # covered by kwargs will get a default from chimera-cam...right?
        if request is not None:
            exptime = request['exptime']
            ftype = request['type']
            # Is this the correct order?
            hbin, vbin = request['binning'].split('x')
            # It seems the bitdepth from the API is buggy... We leave it at
            # its 16bit default. Next!
        else:
            exptime = kwargs['exptime']
            ftype = kwargs['type']
            hbin, vbin = kwargs['binning'].split('x')
        self.thecam.set_flushes(8)
        self.thecam.set_image_binning(hbin, vbin)
        self.thecam.set_exposure(exptime, frametype=ftype)
        # Signal the event
        self.exposeBegin(request)
        # All set up, shoot. This method returns immediately.
        self.thecam.start_exposure()

    def abortExposure(self, readout=True):
        """
        .. method:: abortExposure(readout=True)

            Try to abort the current exposure, reading out the current
            frame if asked to.

            :keyword readout: Whether to readout the current frame after
                                           abort, or loose the photons forever.
                                           Default is True.
            :type readout: bool

            :return: True if successful, False otherwise.
            :rtype: bool
        """
        self.thecam.abort_exposure()
        if readout:
            return self.thecam.fetch_image()

    def isExposing(self):
        if not self.thecam.get_exposure_timeleft():
            return True
        else:
            return False

    # Header
    # def getMetadata(self, request):
    #     return [
    #             ('FWHEEL', str(self['filter_wheel_model']), 'FilterWheel Model'),
    #             ('FILTER', str(self.getFilter()),
    #              'Filter used for this observation')
    #             ]
