from __future__ import print_function
import logging
import time

from chimera.instruments.fli.flidrv.camera import USBCamera

from chimera.instruments.camera import CameraBase

from chimera.interfaces.camera import (CCD, CameraFeature,
                                       ReadoutMode,
                                       CameraStatus)

from chimera.core.lock import lock

import datetime as dt

log = logging.getLogger(__name__)


class FLI(CameraBase):

    """
    .. class:: FLI(CameraBase)

        High level driver for Finger Lakes instruments cameras.
        Uses the python fli bindings to the FLI provided library.
    """

    # Some of the config values were taken from the specs for the cam & CCD.
    __config__ = dict(device="USB",
                      ccd=CCD.IMAGING,
                      temp_delta=2.0,
                      ccd_saturation_level=100000,
                      camera_model="Finger Lakes Instrumentation PL4240",
                      ccd_model="E2V CCD42-40",
                      telescope_focal_length=80000,
                      gain=1)

    def __init__(self):
        """Constructor."""
        CameraBase.__init__(self)
        # FilterWheelBase.__init__(self)

        self.mode = 0
        self._supports = {CameraFeature.TEMPERATURE_CONTROL: True,
                          CameraFeature.PROGRAMMABLE_GAIN: False,
                          CameraFeature.PROGRAMMABLE_OVERSCAN: True,
                          CameraFeature.PROGRAMMABLE_FAN: True,
                          CameraFeature.PROGRAMMABLE_LEDS: True,
                          CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False}

        # my internal CCD code
        self._MY_CCD = 1 << 1
        self._MY_ADC = 1 << 2
        self._MY_READOUT_MODE = 1 << 3

        self._ccds = {self._MY_CCD: CCD.IMAGING}

        self._adcs = {"12 bits": self._MY_ADC}

        self._binnings = {"1x1": self._MY_READOUT_MODE}

        self._binning_factors = {"1x1": 1}

        # Kludge: this is a camera class, let's assume we're talking to a
        # camera!
        self._cams = USBCamera.find_devices()
        if self._cams == []:
            self.log.critical('No devices on USB bus! Exit...')
            return None
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
        self.pixelWidth, self.pixelHeight = self.info['pixel_size']
        self.log.info('Camera: %s', self.info)

        readoutMode = ReadoutMode()
        readoutMode.mode = 0
        readoutMode.gain = 1.0
        readoutMode.width = self.width
        readoutMode.height = self.height
        readoutMode.pixelWidth = self.pixelWidth
        readoutMode.pixelHeight = self.pixelHeight
        self._readoutModes = {self._MY_CCD:
                              {self._MY_READOUT_MODE: readoutMode}}

    def __stop__(self):
        pass

    def getSize(self):
        """
        Return the current CCD size.

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

    def startCooling(self, tempC):
        """
        .. method:: startCooling(tempC)

            Start cooling the camera with SetPoint set to tempC.

            :param int tempC: SetPoint temperature in degrees Celsius.

            :return: True if successful, False otherwise.
            :rtype: bool
        """
        pass

    def stopCooling(self):
        """
        .. method:: stopCooling()

            Stop cooling the camera

            :return: True if successful, False otherwise.
            :rtype: bool
        """
        pass

    def isCooling(self):
        """
        .. method:: isCooling()

            Returns whether the camera is currently cooling.

            :return: True if cooling, False otherwise.
            :rtype: bool
        """
        pass

    @lock
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
        pass

    def startFan(self, rate=None):
        pass

    def stopFan(self):
        pass

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
        '''
        Provisory. Just so info will work!
        '''
        return self._ccds

    def getCurrentCCD(self):
        return self._MY_CCD

    def getBinnings(self):
        return self._binnings

    def getADCs(self):
        # Also provisory! Justo so info will work...
        return self._adcs

    def getPhysicalSize(self):
        return self.width, self.height

    def getOverscanSize(self):
        # Provisory
        return 0, 0

    def getReadoutModes(self):
        """
        .. method:: getReadoutModes()

            Get readout modes supported by this camera.
            The return value would have the following format:
            {ccd1: {mode1: ReadoutMode(), mode2: ReadoutMode2()},
            ccd2: {mode1: ReadoutMode(), mode2: ReadoutMode2()}}

            :return: dict of dicts describing per ccd modes.
        """
        return self._readoutModes

    def _expose(self, request, **kwargs):
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
        ftype = 'normal'
        if request is not None:
            # debug
            self.log.debug('ImageRequest received')
            exptime = int(request['exptime'])
            self.log.debug(request)
            if request['type'] == 'bias' or request['type'] == 'dark':
                ftype = 'dark'  # request['type']
            # Is this the correct order?
            if request['binning']:
                hbin, vbin = request['binning'].split('x')
            else:
                hbin, vbin = 1, 1
            # It seems the bitdepth from the API is buggy... We leave it at
            # its 16bit default. Next!
        else:
            # exptime translation
            exptime = int(kwargs['exptime'])
            # ftype translation; onli dark and normal!
            if kwargs['type'] == 'skyflat':
                ftype = 'normal'
            elif kwargs['type'] == 'bias':
                ftype = 'normal'
                exptime = 0
            elif kwargs['type'] == 'flat':
                ftype = 'normal'
            else:
                ftype = 'dark'
            hbin, vbin = [1, 1]

        self.log.debug('Setting flush of the CCD to 1...')
        self.thecam.set_flushes(1)
        self.log.debug('Setting binning of the CCD to %ix%i...' % (hbin, vbin))
        self.thecam.set_image_binning(hbin, vbin)
        self.log.debug(
            'Setting exposure time to %f and frametype to %s...' % (exptime, ftype))
        self.thecam.set_exposure(exptime * 1000, ftype)  # miliseconds
        # self.log.debug(request)
        # Signal the event
        # return 0

        self.exposeBegin(request)
        # All set up, shoot. This method returns immediately.
        self.log.debug('Starting exposure...')
        self.thecam.start_exposure()

        status = CameraStatus.OK
        self.lastFrameStartTime = dt.datetime.utcnow()
        self.lastFrameTemp = self.getTemperature()

        timestart = time.time()

        while self.isExposing():

            self.log.debug('Exposing ...')

            # [ABORT POINT]
            if self.abort.isSet():
                # [TIAGO] Need to do some cleaning at camera level?
                status = CameraStatus.ABORTED
                break
            elif ((time.time() - timestart) > 2.0 * exptime):
                self.log.warning('Exposure timed-out')
                status = CameraStatus.ABORTED
                break
            # this sleep is EXTREMELY important: without it, Python would stuck
            # on this thread and abort will not work.
            time.sleep(5.0)

        self.exposeComplete(request, status)
        return True

        # end exposure and returns
    # return self._endExposure(imageRequest, status)

    def _readout(self, imageRequest):

        (mode, binning, top,  left,
         width, height) = self._getReadoutModeInfo(imageRequest["binning"],
                                                   imageRequest["window"])
        # readout
        #img = N.zeros((height, width), N.int32)

        self.readoutBegin(imageRequest)

        # [TIAGO] : I think this function must be either thread/locked
        # or re-writed so that it enables chimera to abort.
        img = self.thecam.fetch_image()

        proxy = self._saveImage(imageRequest, img,
                                {"frame_temperature": self.lastFrameTemp,
                                 "frame_start_time": self.lastFrameStartTime,
                                 "binning_factor": self._binning_factors[binning]})

        self.log.debug('Sleeping for 5 seconds so camera can recover...')
        time.sleep(5)
        self.readoutComplete(proxy, CameraStatus.OK)
        return proxy

    # def abortExposure(self, readout=True):
    #     """
    #     Abort the current exposure, reading out the current frame if asked to.
    #     .. method:: abortExposure(readout=True)

    #         :keyword readout: Whether to readout the current frame after
    #                                        abort, or loose the photons forever.
    #                                        Default is True.
    #         :type readout: bool

    #         :return: True if successful, False otherwise.
    #         :rtype: bool
    #     """
    #     self.thecam.abort_exposure()
    #     if readout:
    #         return self.thecam.fetch_image()

    def isExposing(self):
        return not (self.thecam.get_exposure_timeleft() == 0)

    # Header
    # def getMetadata(self, request):
    #     return [
    #             ('FWHEEL', str(self['filter_wheel_model']), 'FilterWheel Model'),
    #             ('FILTER', str(self.getFilter()),
    #              'Filter used for this observation')
    #             ]

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            return False
