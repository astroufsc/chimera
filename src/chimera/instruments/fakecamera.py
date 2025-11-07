# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime as dt
import os
import random
import shutil
import time
import urllib.parse
import urllib.request

import numpy as np
from astropy.io import fits

from chimera.core.lock import lock
from chimera.instruments.camera import CameraBase
from chimera.interfaces.camera import CameraFeature, CameraStatus, ReadoutMode
from chimera.util.position import Epoch, Position


class FakeCamera(CameraBase):

    __config__ = {"use_dss": True, "ccd_width": 512, "ccd_height": 512}

    def __init__(self):
        CameraBase.__init__(self)

        self.__cooling = False

        self.__temperature = 20.0
        self.__setpoint = 0
        self.__last_frame_start = 0
        self.__is_fanning = False

        # my internal CCD code
        self._my_adc = 1 << 2
        self._my_readout_mode = 1 << 3

        self._adcs = {"12 bits": self._my_adc}

        self._binnings = {"1x1": self._my_readout_mode}

        self._binning_factors = {"1x1": 1}

        self._supports = {
            CameraFeature.TEMPERATURE_CONTROL: True,
            CameraFeature.PROGRAMMABLE_GAIN: False,
            CameraFeature.PROGRAMMABLE_OVERSCAN: False,
            CameraFeature.PROGRAMMABLE_FAN: False,
            CameraFeature.PROGRAMMABLE_LEDS: True,
            CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False,
        }

        readout_mode = ReadoutMode()
        readout_mode.mode = 0
        readout_mode.gain = 1.0
        readout_mode.width = 1024
        readout_mode.height = 1024
        readout_mode.pixel_width = 9.0
        readout_mode.pixel_height = 9.0

        self._readout_modes = {self._my_readout_mode: readout_mode}

    def __start__(self):
        self["camera_model"] = "Fake Cameras Inc."
        self["ccd_model"] = "Fake CCDs Inc."

        self.set_hz(2)

    def control(self):
        if self.is_cooling():
            if self.__temperature > self.__setpoint:
                self.__temperature -= 0.5

        return True

    def _expose(self, image_request):
        self.expose_begin(image_request)

        status = CameraStatus.OK

        t = 0
        self.__last_frame_start = dt.datetime.now(dt.timezone.utc)
        while t < image_request["exptime"]:
            # [ABORT POINT]
            if self.abort.is_set():
                status = CameraStatus.ABORTED
                break

            time.sleep(0.1)
            t += 0.1

        time.sleep(0.1)  # simulate shutter close time
        self.expose_complete(image_request, status)

    def make_dark(self, shape, dtype, exptime):
        ret = np.zeros(shape, dtype=dtype)
        # Taken from specs for KAF-1603ME as found in ST-8XME
        # normtemp is now in ADU/pix/sec
        normtemp = ((10 * 2 ** ((self.__temperature - 25) / 6.3)) * exptime) / 2.3
        ret += normtemp + np.random.random(shape)  # +/- 1 variance in readout
        return ret

    def make_flat(self, shape, dtype):
        """
        Flat is composition of:
         - a normal distribution of mean=1000, sigma=1
         - plus a pixel sensitivity constant, which is axis dependent
         - plus a bad region with different mean level
        """

        iadd = 15.0 // shape[0]
        jadd = 10.0 // shape[1]

        badlevel = 0

        badareai = shape[0] // 2
        badareaj = shape[1] // 2

        # this array is only to make sure we create our array
        # with the right dtype
        ret = np.zeros(shape, dtype=dtype)

        ret += np.random.normal(1000, 1, shape)
        ret += np.fromfunction(lambda i, j: i * iadd - j * jadd, shape)

        ret[badareai:, badareaj:] += badlevel

        return ret

    def _readout(self, image_request):
        pix = None
        telescope = None
        dome = None

        (mode, binning, top, left, width, height) = self._get_readout_mode_info(
            image_request["binning"], image_request["window"]
        )
        self.readout_begin(image_request)

        telescope = self.get_proxy("/Telescope/0")
        if not telescope.ping():
            telescope = None

        dome = self.get_proxy("/Dome/0")
        if not dome.ping():
            dome = None

        if not telescope:
            self.log.debug("FakeCamera couldn't find telescope.")
        if not dome:
            self.log.debug("FakeCamera couldn't find dome.")

        ccd_width, ccd_height = self.get_physical_size()

        if image_request["type"].upper() == "DARK":
            self.log.info("making dark")
            pix = self.make_dark(
                (ccd_height, ccd_width), np.float32, image_request["exptime"]
            )
        elif image_request["type"].upper() == "FLAT":
            self.log.info("making flat")
            pix = self.make_flat((ccd_height, ccd_width), np.float32) / 1000
        elif image_request["type"].upper() == "BIAS":
            self.log.info("making bias")
            pix = self.make_dark((ccd_height, ccd_width), np.float32, 0)
        else:
            if telescope and dome:
                self.log.debug("Dome open? " + str(dome.is_slit_open()))

                if dome.is_slit_open() and self["use_dss"]:
                    dome_az = dome.get_az()
                    tel_az = telescope.get_az()

                    tel_position = Position.from_ra_dec(
                        *telescope.get_position_ra_dec(), epoch=Epoch.NOW
                    )
                    tel_position = tel_position.to_epoch(Epoch.J2000)

                    self.log.debug(
                        "Dome AZ: " + str(dome_az) + "  Tel AZ: " + str(tel_az)
                    )
                    if abs(dome_az - tel_az) <= 3:
                        self.log.debug("Dome & Slit aligned -- getting DSS")
                        url = "http://stdatu.stsci.edu/cgi-bin/dss_search?"
                        ra, dec = telescope.get_position_ra_dec()
                        query_args = {
                            "r": ra * 15,  # convert RA from hours to degrees
                            "d": dec,
                            "f": "fits",
                            "e": "j2000",
                            "c": "gz",
                            "fov": "NONE",
                        }

                        # use POSS2-Red surbey ( -90 < d < -20 ) if below -25 deg declination, else use POSS1-Red (-30 < d < +90)
                        # http://www-gsss.stsci.edu/SkySurveys/Surveys.htm
                        if tel_position.dec.deg < -25:
                            query_args["v"] = "poss2ukstu_red"
                            query_args["h"] = (
                                ccd_height / 59.5
                            )  # ~1"/pix (~60 pix/arcmin) is the plate scale of DSS POSS2-Red
                            query_args["w"] = ccd_width / 59.5
                        else:
                            query_args["v"] = "poss1_red"
                            query_args["h"] = (
                                ccd_height / 35.3
                            )  # 1.7"/pix (35.3 pix/arcmin) is the plate scale of DSS POSS1-Red
                            query_args["w"] = ccd_width / 35.3

                        url += urllib.parse.urlencode(query_args)

                        self.log.debug("Attempting URL: " + url)
                        try:
                            t0 = time.time()
                            dssfile = urllib.request.urlretrieve(url)[0]
                            self.log.debug("download took: %.3f s" % (time.time() - t0))
                            fitsfile = dssfile + ".fits.gz"
                            shutil.copy(dssfile, fitsfile)
                            hdulist = fits.open(fitsfile)
                            pix = hdulist[0].data
                            hdulist.close()
                            os.remove(fitsfile)
                        except Exception as e:
                            self.log.warning(
                                "General error getting DSS image: " + str(e)
                            )

                    # dome not aligned, take a 'dome flat'
                    else:
                        self.log.debug("Dome not aligned... making flat image...")
                        try:
                            pix = (
                                self.make_flat((ccd_height, ccd_width), np.float32)
                                / 1000
                            )
                        except Exception as e:
                            self.log.warning("Error generating flat: " + str(e))

        # without telescope/dome, or if dome/telescope aren't aligned, or the dome is closed
        # or we otherwise failed, just make a flat pattern with dark noise
        if pix is None:
            try:
                self.log.info(
                    "Making flat image: " + str(ccd_height) + "x" + str(ccd_width)
                )
                pix = self.make_flat((ccd_height, ccd_width), np.float32)
            except Exception as e:
                self.log.warning("Make flat error: " + str(e))

        # Last resort if nothing else could make a picture
        if pix is None:
            pix = np.zeros((ccd_height, ccd_width), dtype=np.int32)

        image = self._save_image(
            image_request,
            pix,
            {
                "frame_start_time": self.__last_frame_start,
                "frame_temperature": self.get_temperature(),
                "binning_factor": self._binning_factors[binning],
            },
        )

        # [ABORT POINT]
        if self.abort.is_set():
            self.readout_complete(None, CameraStatus.ABORTED)
            return None

        time.sleep(0.1)  # simulate readout time
        self.readout_complete(image.url(), CameraStatus.OK)
        return image

    @lock
    def start_cooling(self, setpoint):
        self.__cooling = True
        self.__setpoint = setpoint
        return True

    @lock
    def stop_cooling(self):
        self.__cooling = False
        return True

    def is_cooling(self):
        return self.__cooling

    @lock
    def get_temperature(self):
        return self.__temperature + random.random()

    def get_set_point(self):
        return self.__setpoint

    @lock
    def start_fan(self, rate=None):
        self.__is_fanning = True

    @lock
    def stop_fan(self):
        self.__is_fanning = False

    def is_fanning(self):
        return self.__is_fanning

    def get_binnings(self):
        return self._binnings

    def get_adcs(self):
        return self._adcs

    def get_physical_size(self):
        return (self["ccd_width"], self["ccd_height"])

    def get_pixel_size(self):
        return (9, 9)

    def get_overscan_size(self):
        return (0, 0)

    def get_readout_modes(self):
        return self._readout_modes

    def supports(self, feature=None):
        return self._supports.get(feature, False)
