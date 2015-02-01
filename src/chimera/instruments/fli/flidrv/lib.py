"""
 Python interface to the FLI (Finger Lakes Instrumentation) API.

 author:       Craig Wm. Versek, Yankee Environmental Systems 
 author_email: cwv@yesinc.com
"""

__author__ = 'Craig Wm. Versek'
__date__ = '2012-07-25'

import os
import sys
from ctypes import cdll, c_char, c_char_p, c_long, c_ulong, c_ubyte, c_int,\
    c_double, c_void_p, c_size_t, POINTER
c_double_p = POINTER(c_double)
c_long_p = POINTER(c_long)

###############################################################################
# Library Definitions
###############################################################################

#   An opaque handle used by library functions to refer to FLI
#   hardware.

FLI_INVALID_DEVICE = -1

flidev_t = c_long

#   The domain of an FLI device.  This consists of a bitwise ORed
#   combination of interface method and device type.  Valid interfaces
#   are \texttt{FLIDOMAIN_PARALLEL_PORT}, \texttt{FLIDOMAIN_USB},
#   \texttt{FLIDOMAIN_SERIAL}, and \texttt{FLIDOMAIN_INET}.  Valid
#   device types are \texttt{FLIDEVICE_CAMERA},
#   \texttt{FLIDOMAIN_FILTERWHEEL}, and \texttt{FLIDOMAIN_FOCUSER}.
#   @see FLIOpen
#   @see FLIList

flidomain_t = c_long

FLIDOMAIN_NONE = 0x00
FLIDOMAIN_PARALLEL_PORT = 0x01
FLIDOMAIN_USB = 0x02
FLIDOMAIN_SERIAL = 0x03
FLIDOMAIN_INET = 0x04
FLIDOMAIN_SERIAL_19200 = 0x05
FLIDOMAIN_SERIAL_1200 = 0x06

FLIDEVICE_NONE = 0x000
FLIDEVICE_CAMERA = 0x100
FLIDEVICE_FILTERWHEEL = 0x200
FLIDEVICE_FOCUSER = 0x300
FLIDEVICE_HS_FILTERWHEEL = 0x0400
FLIDEVICE_RAW = 0x0f00
FLIDEVICE_ENUMERATE_BY_CONNECTION = 0x8000

#   The frame type for an FLI CCD camera device.  Valid frame types are
#   \texttt{FLI_FRAME_TYPE_NORMAL} and \texttt{FLI_FRAME_TYPE_DARK}.
#   @see FLISetFrameType

fliframe_t = c_long

FLI_FRAME_TYPE_NORMAL = 0
FLI_FRAME_TYPE_DARK = 1
FLI_FRAME_TYPE_FLOOD = 2
FLI_FRAME_TYPE_RBI_FLUSH = FLI_FRAME_TYPE_FLOOD | FLI_FRAME_TYPE_DARK

#   The gray-scale bit depth for an FLI camera device.  Valid bit
#   depths are \texttt{FLI_MODE_8BIT} and \texttt{FLI_MODE_16BIT}.
#   @see FLISetBitDepth

flibitdepth_t = c_long

FLI_MODE_8BIT = flibitdepth_t(0)
FLI_MODE_16BIT = flibitdepth_t(1)

#   Type used for shutter operations for an FLI camera device.  Valid
#   shutter types are \texttt{FLI_SHUTTER_CLOSE},
#   \texttt{FLI_SHUTTER_OPEN},
#   \texttt{FLI_SHUTTER_EXTERNAL_TRIGGER},
#   \texttt{FLI_SHUTTER_EXTERNAL_TRIGGER_LOW}, and
#   \texttt{FLI_SHUTTER_EXTERNAL_TRIGGER_HIGH}.
#   @see FLIControlShutter

flishutter_t = c_long

FLI_SHUTTER_CLOSE = 0x0000
FLI_SHUTTER_OPEN = 0x0001
FLI_SHUTTER_EXTERNAL_TRIGGER = 0x0002
FLI_SHUTTER_EXTERNAL_TRIGGER_LOW = 0x0002
FLI_SHUTTER_EXTERNAL_TRIGGER_HIGH = 0x0004
FLI_SHUTTER_EXTERNAL_EXPOSURE_CONTROL = 0x0008

#   Type used for background flush operations for an FLI camera device.  Valid
#   bgflush types are \texttt{FLI_BGFLUSH_STOP} and
#   \texttt{FLI_BGFLUSH_START}.
#   @see FLIControlBackgroundFlush

flibgflush_t = c_long

FLI_BGFLUSH_STOP = 0x0000
FLI_BGFLUSH_START = 0x0001

#   Type used to determine which temperature channel to read.  Valid
#   channel types are \texttt{FLI_TEMPERATURE_INTERNAL} and
#   \texttt{FLI_TEMPERATURE_EXTERNAL}.
#   @see FLIReadTemperature

flichannel_t = c_long

FLI_TEMPERATURE_INTERNAL = 0x0000
FLI_TEMPERATURE_EXTERNAL = 0x0001
FLI_TEMPERATURE_CCD = 0x0000
FLI_TEMPERATURE_BASE = 0x0001

#   Type specifying library debug levels.  Valid debug levels are
#   \texttt{FLIDEBUG_NONE}, \texttt{FLIDEBUG_INFO},
#   \texttt{FLIDEBUG_WARN}, and \texttt{FLIDEBUG_FAIL}.
#   @see FLISetDebugLevel

flidebug_t = c_long
flimode_t = c_long
flistatus_t = c_long
flitdirate_t = c_long
flitdiflags_t = c_long

# Status settings
FLI_CAMERA_STATUS_UNKNOWN = 0xffffffff
FLI_CAMERA_STATUS_MASK = 0x00000003
FLI_CAMERA_STATUS_IDLE = 0x00
FLI_CAMERA_STATUS_WAITING_FOR_TRIGGER = 0x01
FLI_CAMERA_STATUS_EXPOSING = 0x02
FLI_CAMERA_STATUS_READING_CCD = 0x03
FLI_CAMERA_DATA_READY = 0x80000000

FLI_FOCUSER_STATUS_UNKNOWN = 0xffffffff
FLI_FOCUSER_STATUS_HOMING = 0x00000004
FLI_FOCUSER_STATUS_MOVING_IN = 0x00000001
FLI_FOCUSER_STATUS_MOVING_OUT = 0x00000002
FLI_FOCUSER_STATUS_MOVING_MASK = 0x00000007
FLI_FOCUSER_STATUS_HOME = 0x00000080
FLI_FOCUSER_STATUS_LIMIT = 0x00000040
FLI_FOCUSER_STATUS_LEGACY = 0x10000000

FLI_FILTER_WHEEL_PHYSICAL = 0x100
FLI_FILTER_WHEEL_VIRTUAL = 0
FLI_FILTER_WHEEL_LEFT = FLI_FILTER_WHEEL_PHYSICAL | 0x00
FLI_FILTER_WHEEL_RIGHT = FLI_FILTER_WHEEL_PHYSICAL | 0x01
FLI_FILTER_STATUS_MOVING_CCW = 0x01
FLI_FILTER_STATUS_MOVING_CW = 0x02
FLI_FILTER_POSITION_UNKNOWN = 0xff
FLI_FILTER_POSITION_CURRENT = 0x200
FLI_FILTER_STATUS_HOMING = 0x00000004
FLI_FILTER_STATUS_HOME = 0x00000080
FLI_FILTER_STATUS_HOME_LEFT = 0x00000080
FLI_FILTER_STATUS_HOME_RIGHT = 0x00000040
FLI_FILTER_STATUS_HOME_SUCCEEDED = 0x00000008

FLIDEBUG_NONE = 0x00
FLIDEBUG_INFO = 0x01
FLIDEBUG_WARN = 0x02
FLIDEBUG_FAIL = 0x04
FLIDEBUG_IO = 0x08
FLIDEBUG_ALL = FLIDEBUG_INFO | FLIDEBUG_WARN | FLIDEBUG_FAIL

FLI_IO_P0 = 0x01
FLI_IO_P1 = 0x02
FLI_IO_P2 = 0x04
FLI_IO_P3 = 0x08

FLI_FAN_SPEED_OFF = 0x00
FLI_FAN_SPEED_ON = 0xffffffff

FLI_EEPROM_USER = 0x00
FLI_EEPROM_PIXEL_MAP = 0x01

FLI_PIXEL_DEFECT_COLUMN = 0x00
FLI_PIXEL_DEFECT_CLUSTER = 0x10
FLI_PIXEL_DEFECT_POINT_BRIGHT = 0x20
FLI_PIXEL_DEFECT_POINT_DARK = 0x30

###############################################################################
# API Function Prototypes
###############################################################################

_API_FUNCTION_PROTOTYPES = [
    # (flidev_t *dev, char *name, flidomain_t domain);
    ("FLIOpen", [POINTER(flidev_t), c_char_p, flidomain_t]),
    # (char *host, flidebug_t level);
    ("FLISetDebugLevel", [c_char_p, flidebug_t]),
    ("FLIClose", [flidev_t]),  # (flidev_t dev);
    ("FLIGetLibVersion", [c_char_p, c_size_t]),  # (char* ver, size_t len);
    # (flidev_t dev, char* model, size_t len);
    ("FLIGetModel", [flidev_t, c_char_p, c_size_t]),
    # (flidev_t dev, double *pixel_x, double *pixel_y);
    ("FLIGetPixelSize", [flidev_t, c_double_p, c_double_p]),
    ("FLIGetHWRevision", [flidev_t, c_long_p]),  # (flidev_t dev, long *hwrev);
    ("FLIGetFWRevision", [flidev_t, c_long_p]),  # (flidev_t dev, long *fwrev);
    ("FLIGetArrayArea", [flidev_t,
                         c_long_p,
                         c_long_p,
                         c_long_p,
                         c_long_p]
     ),  # (flidev_t dev, long* ul_x, long* ul_y,long* lr_x, long* lr_y);
    ("FLIGetVisibleArea", [flidev_t,
                           c_long_p,
                           c_long_p,
                           c_long_p,
                           c_long_p]
     ),  # (flidev_t dev, long* ul_x, long* ul_y,long* lr_x, long* lr_y);
    ("FLISetExposureTime", []),  # (flidev_t dev, long exptime);
    ("FLISetImageArea", [flidev_t,
                         c_long,
                         c_long,
                         c_long,
                         c_long]
     ),  # (flidev_t dev, long ul_x, long ul_y, long lr_x, long lr_y);
    ("FLISetHBin", [flidev_t, c_long]),  # (flidev_t dev, long hbin);
    ("FLISetVBin", [flidev_t, c_long]),  # (flidev_t dev, long vbin);
    # (flidev_t dev, fliframe_t frametype);
    ("FLISetFrameType", [flidev_t, fliframe_t]),
    ("FLICancelExposure", [flidev_t]),  # (flidev_t dev);
    # (flidev_t dev, long *timeleft);
    ("FLIGetExposureStatus", [flidev_t, c_long_p]),
    # (flidev_t dev, double temperature);
    ("FLISetTemperature", [flidev_t, c_double]),
    # (flidev_t dev, double *temperature);
    ("FLIGetTemperature", [flidev_t, c_double_p]),
    # (flidev_t dev, double *power);
    ("FLIGetCoolerPower", [flidev_t, c_double_p]),
    # (flidev_t dev, void *buff, size_t width);
    ("FLIGrabRow", [flidev_t, c_void_p, c_size_t]),
    ("FLIExposeFrame", [flidev_t]),  # (flidev_t dev);
    # (flidev_t dev, long rows, long repeat);
    ("FLIFlushRow", [flidev_t, c_long, c_long]),
    ("FLISetNFlushes", [flidev_t, c_long]),  # (flidev_t dev, long nflushes);
    # (flidev_t dev, flibitdepth_t bitdepth);
    ("FLISetBitDepth", [flidev_t, flibitdepth_t]),
    # (flidev_t dev, long *ioportset);
    ("FLIReadIOPort", [flidev_t, c_long_p]),
    ("FLIWriteIOPort", [flidev_t, c_long]),  # (flidev_t dev, long ioportset);
    # (flidev_t dev, long ioportset);
    ("FLIConfigureIOPort", [flidev_t, c_long]),
    ("FLILockDevice", [flidev_t]),  # (flidev_t dev);
    ("FLIUnlockDevice", [flidev_t]),  # (flidev_t dev);
    # (flidev_t dev, flishutter_t shutter);
    ("FLIControlShutter", [flidev_t, flishutter_t]),
    # (flidev_t dev, flibgflush_t bgflush);
    ("FLIControlBackgroundFlush", [flidev_t, flibgflush_t]),
    # (flidev_t dev, unsigned long dacset);
    ("FLISetDAC", [flidev_t, c_ulong]),
    ("FLIList", [flidomain_t,
                 POINTER(POINTER(c_char_p))]
     ),  # (flidomain_t domain, char ***names);
    ("FLIFreeList", [POINTER(c_char_p)]),  # (char **names);
    # Filter Wheels
    ("FLIGetFilterName", [flidev_t,
                          c_long,
                          c_char_p,
                          c_size_t]
     ),  # (flidev_t dev, long filter, char *name, size_t len);
    ("FLISetActiveWheel", [flidev_t, c_long]),  # (flidev_t dev, long wheel);
    # (flidev_t dev, long *wheel);
    ("FLIGetActiveWheel", [flidev_t, c_long_p]),
    ("FLISetFilterPos", [flidev_t, c_long]),  # (flidev_t dev, long filter);
    ("FLIGetFilterPos", [flidev_t, c_long_p]),  # (flidev_t dev, long *filter);
    # (flidev_t dev, long *filter);
    ("FLIGetFilterCount", [flidev_t, c_long_p]),
    # Focusers
    ("FLIStepMotor", [flidev_t, c_long]),  # (flidev_t dev, long steps);
    ("FLIStepMotorAsync", [flidev_t, c_long]),  # (flidev_t dev, long steps);
    # (flidev_t dev, long *position);
    ("FLIGetStepperPosition", [flidev_t, c_long_p]),
    # (flidev_t dev, long *steps);
    ("FLIGetStepsRemaining", [flidev_t, c_long_p]),
    ("FLIHomeFocuser", [flidev_t]),  # (flidev_t dev);
    ("FLICreateList", [flidomain_t]),  # (flidomain_t domain);
    ("FLIDeleteList", []),  # (void);
    ("FLIListFirst", [POINTER(flidomain_t),
                      c_char_p,
                      c_size_t,
                      c_char_p,
                      c_size_t]
     ),  # (flidomain_t *domain, char *filename,size_t fnlen, char *name, size_t namelen);
    ("FLIListNext", [POINTER(flidomain_t),
                     c_char_p,
                     c_size_t,
                     c_char_p,
                     c_size_t]
     ),  # (flidomain_t *domain, char *filename,size_t fnlen, char *name, size_t namelen);
    ("FLIReadTemperature", [flidev_t,
                            flichannel_t,
                            c_double_p]
     ),  # (flidev_t dev,flichannel_t channel, double *temperature);
    # (flidev_t dev, long *extent);
    ("FLIGetFocuserExtent", [flidev_t, c_long_p]),
    # (flidev_t dev, int ep, void *buf, long *len);
    ("FLIUsbBulkIO", [flidev_t, c_int, c_void_p, c_long_p]),
    # (flidev_t dev, long *status);
    ("FLIGetDeviceStatus", [flidev_t, c_long_p]),
    ("FLIGetCameraModeString", [flidev_t,
                                flimode_t,
                                c_char_p,
                                c_size_t]
     ),  # (flidev_t dev, flimode_t mode_index, char *mode_string, size_t siz);
    # (flidev_t dev, flimode_t *mode_index);
    ("FLIGetCameraMode", [flidev_t, POINTER(flimode_t)]),
    # (flidev_t dev, flimode_t mode_index);
    ("FLISetCameraMode", [flidev_t, flimode_t]),
    ("FLIHomeDevice", [flidev_t]),  # (flidev_t dev);
    ("FLIGrabFrame", [flidev_t,
                      c_void_p,
                      c_size_t,
                      POINTER(c_size_t)]),  # (flidev_t dev, void* buff, size_t buffsize, size_t* bytesgrabbed);
    # (flidev_t dev, flitdirate_t tdi_rate, flitdiflags_t flags);
    ("FLISetTDI", [flidev_t, flitdirate_t, flitdiflags_t]),
    # (flidev_t dev, void *buff, size_t size);
    ("FLIGrabVideoFrame", [flidev_t, c_void_p, c_size_t]),
    ("FLIStopVideoMode", [flidev_t]),  # (flidev_t dev);
    ("FLIStartVideoMode", [flidev_t]),  # (flidev_t dev);
    # (flidev_t dev, char* serial, size_t len);
    ("FLIGetSerialString", [flidev_t, c_char_p, c_size_t]),
    ("FLIEndExposure", [flidev_t]),  # (flidev_t dev);
    ("FLITriggerExposure", [flidev_t]),  # (flidev_t dev);
    ("FLISetFanSpeed", [flidev_t, c_long]),  # (flidev_t dev, long fan_speed);
    ("FLISetVerticalTableEntry", [flidev_t,
                                  c_long,
                                  c_long,
                                  c_long,
                                  c_long]
     ),  # (flidev_t dev, long index, long height, long bin, long mode);
    ("FLIGetVerticalTableEntry", [flidev_t,
                                  c_long,
                                  c_long_p,
                                  c_long_p,
                                  c_long_p]
     ),  # (flidev_t dev, long index, long *height, long *bin, long *mode);
    ("FLIGetReadoutDimensions", [flidev_t,
                                 c_long_p,
                                 c_long_p,
                                 c_long_p,
                                 c_long_p,
                                 c_long_p,
                                 c_long_p]
     ),  # (flidev_t dev, long *width, long *hoffset, long *hbin, long *height, long *voffset, long *vbin);
    ("FLIEnableVerticalTable", [flidev_t,
                                c_long,
                                c_long,
                                c_long, ]
     ),  # (flidev_t dev, long width, long offset, long flags);
    ("FLIReadUserEEPROM", [flidev_t,
                           c_long,
                           c_long,
                           c_long,
                           c_void_p]
     ),  # (flidev_t dev, long loc, long address, long length, void *rbuf);
    ("FLIWriteUserEEPROM", [flidev_t,
                            c_long,
                            c_long,
                            c_long,
                            c_void_p]),  # (flidev_t dev, long loc, long address, long length, void *wbuf);
]
###############################################################################
# Error Handling
###############################################################################


class FLIError(Exception):
    pass


class FLIWarning(Warning):
    pass


def chk_err(err):
    """wraps a libfli C function call with error checking code"""
    if err < 0:
        msg = os.strerror(abs(err))  # err is always negative
        raise FLIError(msg)
    if err > 0:
        msg = os.strerror(err)  # FIXME, what if err is positive?
        raise FLIWarning(msg)
    return err

###############################################################################
# Library Loader
###############################################################################
LIBVERSIZ = 1024


class FLILibrary:
    __dll = None

    @staticmethod
    def getDll(debug=False,
               wrap_error_codes=True,
               ):
        if FLILibrary.__dll is None:
            if sys.platform == 'linux2':
                FLILibrary.__dll = cdll.LoadLibrary("libfli.so")
            elif sys.platform == 'win32':  # FIXME this hasn't been tested yet
                from ctypes import windll
                FLILibrary.__dll = windll.LoadLibrary("libfli")
            else:
                # try loading the library anyway
                raise RuntimeError("Platform not supported")
            # wrap the api functions
            for api_func_name, argtypes in _API_FUNCTION_PROTOTYPES:
                api_func = FLILibrary.__dll.__getattr__(api_func_name)
                api_func.argtypes = argtypes
                if wrap_error_codes:
                    api_func.restype = chk_err

        # set debug level
        if debug:
            FLILibrary.__dll.FLISetDebugLevel(None, FLIDEBUG_ALL)

        return FLILibrary.__dll

    @staticmethod
    def getVersion():
        libfli = FLILibrary.getDll()
        c_buff = c_char * LIBVERSIZ
        libver = c_buff()
        libfli.FLIGetLibVersion(libver, LIBVERSIZ)
        return libver.value

###############################################################################
#  TEST CODE
###############################################################################
if __name__ == "__main__":
    libfli = FLILibrary.getDll(debug=True)
