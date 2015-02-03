import sys
import time

try:
    from collections import OrderedDict
except ImportError:
    from odict import OrderedDict

from ctypes import pointer, POINTER, byref, sizeof, Structure, c_char,\
    c_char_p, c_long, c_ubyte, c_uint8, c_uint16, c_double

import numpy

from lib import FLILibrary, FLIError, FLIWarning, flidomain_t, flidev_t,\
    fliframe_t, FLIDOMAIN_USB, FLIDEVICE_CAMERA,\
    FLI_FRAME_TYPE_NORMAL, FLI_FRAME_TYPE_DARK,\
    FLI_FRAME_TYPE_RBI_FLUSH, FLI_MODE_8BIT, FLI_MODE_16BIT,\
    FLI_TEMPERATURE_CCD, FLI_TEMPERATURE_BASE

from device import USBDevice
"""
USB camera class.

.. class:: USBCamera
Object-oriented interface for handling FLI USB cameras

 author:       Craig Wm. Versek, Yankee Environmental Systems 
 author_email: cwv@yesinc.com
"""

__author__ = 'Craig Wm. Versek'
__date__ = '2012-08-08'

###############################################################################
DEBUG = False
###############################################################################


class USBCamera(USBDevice):
    # load the DLL
    _libfli = FLILibrary.getDll(debug=DEBUG)
    _domain = flidomain_t(FLIDOMAIN_USB | FLIDEVICE_CAMERA)

    def __init__(self, dev_name, model, bitdepth='16bit'):
        USBDevice.__init__(self, dev_name=dev_name, model=model)
        self.hbin = 1
        self.vbin = 1
        self.bitdepth = bitdepth
        self.set_bitdepth(bitdepth)

    def get_info(self):
        info = OrderedDict()
        tmp1, tmp2, tmp3, tmp4 = (c_long(), c_long(), c_long(), c_long())
        d1, d2 = (c_double(), c_double())
        info['serial_number'] = self.get_serial_number()
        self._libfli.FLIGetHWRevision(self._dev, byref(tmp1))
        info['hardware_rev'] = tmp1.value
        self._libfli.FLIGetFWRevision(self._dev, byref(tmp1))
        info['firmware_rev'] = tmp1.value
        self._libfli.FLIGetPixelSize(self._dev, byref(d1), byref(d2))
        info['pixel_size'] = (d1.value, d2.value)
        self._libfli.FLIGetArrayArea(
            self._dev, byref(tmp1), byref(tmp2), byref(tmp3), byref(tmp4))
        info['array_area'] = (tmp1.value, tmp2.value, tmp3.value, tmp4.value)
        self._libfli.FLIGetVisibleArea(
            self._dev, byref(tmp1), byref(tmp2), byref(tmp3), byref(tmp4))
        info['visible_area'] = (tmp1.value, tmp2.value, tmp3.value, tmp4.value)
        return info

    def get_image_size(self):
        "returns (row_width, img_rows, img_size)"
        left, top, right, bottom = (c_long(), c_long(), c_long(), c_long())
        self._libfli.FLIGetVisibleArea(
            self._dev, byref(left), byref(top), byref(right), byref(bottom))
        row_width = (right.value - left.value) / self.hbin
        img_rows = (bottom.value - top.value) / self.vbin
        img_size = img_rows * row_width * sizeof(c_uint16)
        return (row_width, img_rows, img_size)

    def set_image_area(self, ul_x, ul_y, lr_x, lr_y):
        # FIXME does this API call actually do anything?
        left, top, right, bottom = (
            c_long(ul_x), c_long(ul_y), c_long(lr_x), c_long(lr_y))
        row_width = (right.value - left.value) / self.hbin
        img_rows = (bottom.value - top.value) / self.vbin
        self._libfli.FLISetImageArea(self._dev, left, top, c_long(
            left.value + row_width), c_long(top.value + img_rows))

    def set_image_binning(self, hbin=1, vbin=1):
        left, top, right, bottom = (c_long(), c_long(), c_long(), c_long())
        self._libfli.FLIGetVisibleArea(
            self._dev, byref(left), byref(top), byref(right), byref(bottom))
        row_width = (right.value - left.value) / hbin
        img_rows = (bottom.value - top.value) / vbin
        self._libfli.FLISetImageArea(
            self._dev, left, top, left.value + row_width, top.value + img_rows)
        self._libfli.FLISetHBin(self._dev, hbin)
        self._libfli.FLISetVBin(self._dev, vbin)
        self.hbin = hbin
        self.vbin = vbin

    def set_flushes(self, num):
        """set the number of flushes to the CCD before taking exposure

           must have 0 <= num <= 16, else raises ValueError
        """
        if not(0 <= num <= 16):
            raise ValueError("must have 0 <= num <= 16")
        self._libfli.FLISetNFlushes(self._dev, c_long(num))

    def set_temperature(self, T):
        "set the camera's temperature target in degrees Celcius"
        self._libfli.FLISetTemperature(self._dev, c_double(T))

    def get_temperature(self):
        "gets the camera's temperature in degrees Celcius"
        T = c_double()
        self._libfli.FLIGetTemperature(self._dev, byref(T))
        return T.value

    def read_CCD_temperature(self):
        "gets the CCD's temperature in degrees Celcius"
        T = c_double()
        self._libfli.FLIReadTemperature(
            self._dev, FLI_TEMPERATURE_CCD, byref(T))
        return T.value

    def read_base_temperature(self):
        "gets the cooler's hot side in degrees Celcius"
        T = c_double()
        self._libfli.FLIReadTemperature(
            self._dev, FLI_TEMPERATURE_BASE, byref(T))
        return T.value

    def get_cooler_power(self):
        "gets the cooler's power in watts (undocumented API function)"
        P = c_double()
        self._libfli.FLIGetCoolerPower(self._dev, byref(P))
        return P.value

    def set_exposure(self, exptime, frametype="normal"):
        """
        Setup the exposure type.

        .. method:: set_exposure(exptime, frametype)
            Set parameters for the next frame.
            :parameter exptime: exposure time in milliseconds
            :keyword frametype: 'normal': open shutter exposure
                                'dark': exposure with shutter closed
                                'rbi_flush': flood CCD with internal light,
                                             with shutter closed
        """
        exptime = c_long(exptime)
        if frametype == "normal":
            frametype = fliframe_t(FLI_FRAME_TYPE_NORMAL)
        elif frametype == "dark":
            frametype = fliframe_t(FLI_FRAME_TYPE_DARK)
        elif frametype == "rbi_flush":
            # FIXME note: FLI_FRAME_TYPE_RBI_FLUSH = FLI_FRAME_TYPE_FLOOD | FLI_FRAME_TYPE_DARK
            # is this always the correct mode?
            frametype = fliframe_t(FLI_FRAME_TYPE_RBI_FLUSH)
        else:
            raise ValueError(
                "'frametype' must be either 'normal','dark' or 'rbi_flush'")
        self._libfli.FLISetExposureTime(self._dev, exptime)
        self._libfli.FLISetFrameType(self._dev, frametype)

    def set_bitdepth(self, bitdepth='8bit'):
        if bitdepth == '8bit':
            pass  # FIXME gives "invalid argument" error from API
            #self._libfli.FLISetBitDepth(self._dev, FLI_MODE_8BIT)
        elif bitdepth == '16bit':
            pass  # FIXME gives "invalid argument" error from API
            #self._libfli.FLISetBitDepth(self._dev, FLI_MODE_16BIT)
        else:
            raise ValueError("'bitdepth' must be either '8bit' or '16bit'")
        self.bitdepth = bitdepth

    def take_photo(self):
        """ Expose the frame, wait for completion, and fetch the image data.
        """
        self.start_exposure()
        # wait for completion
        while True:
            timeleft = self.get_exposure_timeleft()
            if timeleft == 0:
                break
            time.sleep(timeleft / 1000.0)  # sleep for milliseconds
        # grab the image
        return self.fetch_image()

    def start_exposure(self):
        """ Begin the exposure and return immediately.
            Use the method  'get_timeleft' to check the exposure progress 
            until it returns 0, then use method 'fetch_image' to fetch the image
            data as a numpy array.
        """
        self._libfli.FLIExposeFrame(self._dev)

    def get_exposure_timeleft(self):
        """
        Return the time left on the exposure in milliseconds.
        """
        timeleft = c_long()
        self._libfli.FLIGetExposureStatus(self._dev, byref(timeleft))
        return timeleft.value

    def cancel_exposure(self):
        """
        Abort the current exposure.

        .. method:: cancel_exposure()
            Stops the current frame no matter the status, discards accumulated
            photons.
        """
        self._libfli.FLICancelExposure(self._dev)

    def end_exposure(self):
        """
        Stop the current exposure.

        .. method:: end_exposure()
            Stops the current exposure, keeps photons (?).
        """
        self._libfli.FLIEndExposure(self._dev)
        # return self.fetch_image()

    def fetch_image(self):
        """ Fetch the image data for the last exposure.
            Returns a numpy.ndarray object.
        """
        row_width, img_rows, img_size = self.get_image_size()
        # use bit depth to determine array data type
        img_array_dtype = None
        img_ptr_ctype = None
        if self.bitdepth == '8bit':
            img_array_dtype = numpy.uint8
            img_ptr_ctype = c_uint8
        elif self.bitdepth == '16bit':
            img_array_dtype = numpy.uint16
            img_ptr_ctype = c_uint16
        else:
            raise FLIError("'bitdepth' must be either '8bit' or '16bit'")
        # allocate numpy array to store image
        img_array = numpy.zeros((img_rows, row_width), dtype=img_array_dtype)
        # get pointer to array's data space
        img_ptr = img_array.ctypes.data_as(POINTER(img_ptr_ctype))
        # grab image buff row by row
        for row in range(img_rows):
            offset = row * row_width * sizeof(img_ptr_ctype)
            self._libfli.FLIGrabRow(
                self._dev, byref(img_ptr.contents, offset), row_width)
        return img_array

###############################################################################
#  TEST CODE
###############################################################################
if __name__ == "__main__":
    cams = USBCamera.find_devices()
    cam0 = cams[0]
    print "info:", cam0.get_info()
    print "image size:", cam0.get_image_size()
    print "temperature:", cam0.get_temperature()
    cam0.set_image_binning(2, 2)
    cam0.set_bitdepth("16bit")
    cam0.set_exposure(5)
    img = cam0.take_photo()
    print img
