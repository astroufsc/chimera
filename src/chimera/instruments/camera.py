# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
import os
import threading
import time
from math import cos, pi, sin

from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.controllers.imageserver.util import get_image_server
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.interfaces.camera import (
    CameraExpose,
    CameraInformation,
    CameraTemperature,
    InvalidReadoutMode,
    Shutter,
)
from chimera.util.image import Image, ImageUtil


class CameraBase(ChimeraObject, CameraExpose, CameraTemperature, CameraInformation):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.abort = threading.Event()
        self.abort.clear()

        self.__is_exposing = threading.Event()

        self.extra_header_info = dict()

    def __stop__(self):
        self.abort_exposure(readout=False)

    def get_extra_header_info(self):
        return self.extra_header_info

    @lock
    def expose(self, request=None, **kwargs):

        self.__is_exposing.set()

        try:
            return self._base_expose(request, **kwargs)
        finally:
            self.__is_exposing.clear()

    def _base_expose(self, request, **kwargs):

        if request:

            if isinstance(request, ImageRequest):
                image_request = request
            elif isinstance(request, dict):
                image_request = ImageRequest(**request)
        else:
            if kwargs:
                image_request = ImageRequest(**kwargs)
            else:
                image_request = ImageRequest()

        frames = image_request["frames"]
        interval = image_request["interval"]

        # validate shutter
        if str(image_request["shutter"]).lower() == "open":
            image_request["shutter"] = Shutter.OPEN
        elif str(image_request["shutter"]).lower() == "close":
            image_request["shutter"] = Shutter.CLOSE
        else:
            image_request["shutter"] = Shutter.LEAVE_AS_IS

        # validate readout mode
        self._get_readout_mode_info(image_request["binning"], image_request["window"])

        # use image server if any and save image on server's default dir if
        # filename given as a relative path.
        server = get_image_server(self)
        if not os.path.isabs(image_request["filename"]):
            image_request["filename"] = os.path.join(
                server.default_night_dir(), image_request["filename"]
            )

        # clear abort setting
        self.abort.clear()

        images = []

        for frame_num in range(frames):

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            image_request.begin_exposure(self)
            self._expose(image_request)

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            image = self._readout(image_request)
            if image is not None:
                images.append(image.url())
                image_request.end_exposure(self)

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            if (interval > 0 and frame_num < frames) and (not frames == 1):
                time.sleep(interval)

        return tuple(images)

    def abort_exposure(self, readout=True):

        if not self.is_exposing():
            return False

        # set our event, so current exposure know that it must abort
        self.abort.set()

        # then wait
        while self.is_exposing():
            time.sleep(0.1)

        return True

    def _save_image(self, image_request, image_data, extras=None):

        if extras is not None:
            self.extra_header_info.update(extras)

        image_request.headers += self.get_metadata(image_request)
        image = Image.create(image_data, image_request)

        # register image on ImageServer

        server = get_image_server(self)
        if server:
            image.http(server.register(image.filename))

        # and finally compress the image if asked
        if image_request["compress_format"].lower() != "no":
            image.compress(format=image_request["compress_format"], multiprocess=True)

        return image

    def _get_readout_mode_info(self, binning, window):
        """
        Check if the given binning and window could be used.

        Returns a tuple (mode_id, binning, top, left, width, height)
        """

        mode = None

        try:
            bin_id = self.get_binnings()[binning]
            mode = self.get_readout_modes()[bin_id]
        except KeyError:
            # use full frame if None given
            bin_id = self.get_binnings()["1x1"]
            mode = self.get_readout_modes()[bin_id]

        left = 0
        top = 0
        width, height = mode.get_size()

        if window is not None:
            try:
                xx, yy = window.split(",")
                xx = xx.strip()
                yy = yy.strip()
                x1, x2 = xx.split(":")
                y1, y2 = yy.split(":")

                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)

                left = min(x1, x2) - 1
                top = min(y1, y2) - 1
                width = (max(x1, x2) - min(x1, x2)) + 1
                height = (max(y1, y2) - min(y1, y2)) + 1

                if left < 0 or left >= mode.width:
                    raise InvalidReadoutMode(
                        f"Invalid subframe: left={left}, ccd width (in this binning)={mode.width}"
                    )

                if top < 0 or top >= mode.height:
                    raise InvalidReadoutMode(
                        f"Invalid subframe: top={top}, ccd height (in this binning)={mode.height}"
                    )

                if width > mode.width:
                    raise InvalidReadoutMode(
                        f"Invalid subframe: width={width}, ccd width (in this binning)={mode.width}"
                    )

                if height > mode.height:
                    raise InvalidReadoutMode(
                        f"Invalid subframe: height={height}, ccd height (in this binning)={mode.height}"
                    )

            except ValueError:
                left = 0
                top = 0
                width, height = mode.get_size()

        if not binning:
            binning = list(self.get_binnings().keys()).pop(
                list(self.get_binnings().keys()).index("1x1")
            )

        return mode, binning, top, left, width, height

    def is_exposing(self):
        return self.__is_exposing.is_set()

    @lock
    def start_cooling(self, temp_c):
        raise NotImplementedError()

    @lock
    def stop_cooling(self):
        raise NotImplementedError()

    def is_cooling(self):
        raise NotImplementedError()

    @lock
    def get_temperature(self):
        raise NotImplementedError()

    @lock
    def get_set_point(self):
        raise NotImplementedError()

    @lock
    def start_fan(self, rate=None):
        raise NotImplementedError()

    @lock
    def stop_fan(self):
        raise NotImplementedError()

    def is_fanning(self):
        raise NotImplementedError()

    def get_binnings(self):
        raise NotImplementedError()

    def get_adcs(self):
        raise NotImplementedError()

    def get_physical_size(self):
        raise NotImplementedError()

    def get_pixel_size(self):
        raise NotImplementedError()

    def get_overscan_size(self):
        raise NotImplementedError()

    def get_readout_modes(self):
        raise NotImplementedError()

    def supports(self, feature=None):
        raise NotImplementedError()

    def get_metadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        md = [
            ("EXPTIME", float(request["exptime"]), "exposure time in seconds"),
            ("IMAGETYP", request["type"].strip(), "Image type"),
            ("SHUTTER", str(request["shutter"]), "Requested shutter state"),
            ("INSTRUME", str(self["camera_model"]), "Name of instrument"),
            ("CCD", str(self["ccd_model"]), "CCD Model"),
            ("CCD_DIMX", self.get_physical_size()[0], "CCD X Dimension Size"),
            ("CCD_DIMY", self.get_physical_size()[1], "CCD Y Dimension Size"),
            ("CCDPXSZX", self.get_pixel_size()[0], "CCD X Pixel Size [micrometer]"),
            ("CCDPXSZY", self.get_pixel_size()[1], "CCD Y Pixel Size [micrometer]"),
        ]

        if request["window"] is not None:
            md += [("DETSEC", request["window"], "Detector coodinates of the image")]

        if "frame_temperature" in list(self.extra_header_info.keys()):
            md += [
                (
                    "CCD-TEMP",
                    self.extra_header_info["frame_temperature"],
                    "CCD Temperature at Exposure Start [deg. C]",
                )
            ]

        if "frame_start_time" in list(self.extra_header_info.keys()):
            md += [
                (
                    "DATE-OBS",
                    ImageUtil.format_date(
                        self.extra_header_info.get("frame_start_time")
                    ),
                    "Date exposure started",
                )
            ]

        mode, binning, top, left, width, height = self._get_readout_mode_info(
            request["binning"], request["window"]
        )
        # Binning keyword: http://iraf.noao.edu/projects/ccdmosaic/imagedef/mosaic/MosaicV1.html
        #    CCD on-chip summing given as two or four integer numbers.  These define
        # the summing of CCD pixels in the amplifier readout order.  The first
        # two numbers give the number of pixels summed in the serial and parallel
        # directions respectively.  If the first pixel read out consists of fewer
        # unbinned pixels along either direction the next two numbers give the
        # number of pixels summed for the first serial and parallel pixels.  From
        # this it is implicit how many pixels are summed for the last pixels
        # given the size of the CCD section (CCDSEC).  It is highly recommended
        # that controllers read out all pixels with the same summing in which
        # case the size of the CCD section will be the summing factors times the
        # size of the data section.
        md += [("CCDSUM", binning.replace("x", " "), "CCD on-chip summing")]

        focal_length = self["telescope_focal_length"]
        if (
            focal_length is not None
        ):  # If there is no telescope_focal_length defined, don't store WCS
            bin_factor = self.extra_header_info.get("binning_factor", 1.0)
            pix_w, pix_h = self.get_pixel_size()
            focal_length = self["telescope_focal_length"]

            scale_x = bin_factor * (((180 / pi) / focal_length) * (pix_w * 0.001))
            scale_y = bin_factor * (((180 / pi) / focal_length) * (pix_h * 0.001))

            full_width, full_height = self.get_physical_size()
            crpix1 = ((int(full_width / 2.0)) - left) - 1
            crpix2 = ((int(full_height / 2.0)) - top) - 1

            # Adding WCS coordinates according to FITS standard.
            # Quick sheet: http://www.astro.iag.usp.br/~moser/notes/GAi_FITSimgs.html
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1061G
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1077C
            md += [
                ("CRPIX1", crpix1, "coordinate system reference pixel"),
                ("CRPIX2", crpix2, "coordinate system reference pixel"),
                (
                    "CD1_1",
                    scale_x * cos(self["rotation"] * pi / 180.0),
                    "transformation matrix element (1,1)",
                ),
                (
                    "CD1_2",
                    -scale_y * sin(self["rotation"] * pi / 180.0),
                    "transformation matrix element (1,2)",
                ),
                (
                    "CD2_1",
                    scale_x * sin(self["rotation"] * pi / 180.0),
                    "transformation matrix element (2,1)",
                ),
                (
                    "CD2_2",
                    scale_y * cos(self["rotation"] * pi / 180.0),
                    "transformation matrix element (2,2)",
                ),
            ]

        return md
