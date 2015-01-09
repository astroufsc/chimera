"""
 FLI.filter_wheel.py

 Object-oriented interface for handling FLI (Finger Lakes Instrumentation)
 USB filter wheels

 author:       Craig Wm. Versek, Yankee Environmental Systems
 author_email: cwv@yesinc.com
"""

__author__ = 'Craig Wm. Versek'
__date__ = '2012-08-16'

import sys
import time

from ctypes import byref, c_char, c_char_p, c_long, c_ubyte, c_double

from lib import FLILibrary, FLIError, FLIWarning, flidomain_t, flidev_t,\
    fliframe_t, FLIDOMAIN_USB, FLIDEVICE_FILTERWHEEL

from device import USBDevice
###############################################################################
DEBUG = False

###############################################################################


class USBFilterWheel(USBDevice):
    # load the DLL
    _libfli = FLILibrary.getDll(debug=DEBUG)
    _domain = flidomain_t(FLIDOMAIN_USB | FLIDEVICE_FILTERWHEEL)

    def __init__(self, dev_name, model):
        USBDevice.__init__(self, dev_name=dev_name, model=model)

    def set_filter_pos(self, pos):
        self._libfli.FLISetFilterPos(self._dev, c_long(pos))

    def get_filter_pos(self):
        pos = c_long()
        self._libfli.FLIGetFilterPos(self._dev, byref(pos))
        return pos.value

    def get_filter_count(self):
        count = c_long()
        self._libfli.FLIGetFilterCount(self._dev, byref(count))
        return count.value


###############################################################################
#  TEST CODE
###############################################################################
if __name__ == "__main__":
    fws = USBFilterWheel.find_devices()
    fw0 = fws[0]
