# This file was created automatically by SWIG 1.3.29.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _sbigudrv
import new
new_instancemethod = new.instancemethod
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'PySwigObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


ENV_WIN = _sbigudrv.ENV_WIN
ENV_WINVXD = _sbigudrv.ENV_WINVXD
ENV_WINSYS = _sbigudrv.ENV_WINSYS
ENV_ESRVJK = _sbigudrv.ENV_ESRVJK
ENV_ESRVWIN = _sbigudrv.ENV_ESRVWIN
ENV_MACOSX = _sbigudrv.ENV_MACOSX
ENV_LINUX = _sbigudrv.ENV_LINUX
TARGET = _sbigudrv.TARGET
CC_NULL = _sbigudrv.CC_NULL
CC_START_EXPOSURE = _sbigudrv.CC_START_EXPOSURE
CC_END_EXPOSURE = _sbigudrv.CC_END_EXPOSURE
CC_READOUT_LINE = _sbigudrv.CC_READOUT_LINE
CC_DUMP_LINES = _sbigudrv.CC_DUMP_LINES
CC_SET_TEMPERATURE_REGULATION = _sbigudrv.CC_SET_TEMPERATURE_REGULATION
CC_QUERY_TEMPERATURE_STATUS = _sbigudrv.CC_QUERY_TEMPERATURE_STATUS
CC_ACTIVATE_RELAY = _sbigudrv.CC_ACTIVATE_RELAY
CC_PULSE_OUT = _sbigudrv.CC_PULSE_OUT
CC_ESTABLISH_LINK = _sbigudrv.CC_ESTABLISH_LINK
CC_GET_DRIVER_INFO = _sbigudrv.CC_GET_DRIVER_INFO
CC_GET_CCD_INFO = _sbigudrv.CC_GET_CCD_INFO
CC_QUERY_COMMAND_STATUS = _sbigudrv.CC_QUERY_COMMAND_STATUS
CC_MISCELLANEOUS_CONTROL = _sbigudrv.CC_MISCELLANEOUS_CONTROL
CC_READ_SUBTRACT_LINE = _sbigudrv.CC_READ_SUBTRACT_LINE
CC_UPDATE_CLOCK = _sbigudrv.CC_UPDATE_CLOCK
CC_READ_OFFSET = _sbigudrv.CC_READ_OFFSET
CC_OPEN_DRIVER = _sbigudrv.CC_OPEN_DRIVER
CC_CLOSE_DRIVER = _sbigudrv.CC_CLOSE_DRIVER
CC_TX_SERIAL_BYTES = _sbigudrv.CC_TX_SERIAL_BYTES
CC_GET_SERIAL_STATUS = _sbigudrv.CC_GET_SERIAL_STATUS
CC_AO_TIP_TILT = _sbigudrv.CC_AO_TIP_TILT
CC_AO_SET_FOCUS = _sbigudrv.CC_AO_SET_FOCUS
CC_AO_DELAY = _sbigudrv.CC_AO_DELAY
CC_GET_TURBO_STATUS = _sbigudrv.CC_GET_TURBO_STATUS
CC_END_READOUT = _sbigudrv.CC_END_READOUT
CC_GET_US_TIMER = _sbigudrv.CC_GET_US_TIMER
CC_OPEN_DEVICE = _sbigudrv.CC_OPEN_DEVICE
CC_CLOSE_DEVICE = _sbigudrv.CC_CLOSE_DEVICE
CC_SET_IRQL = _sbigudrv.CC_SET_IRQL
CC_GET_IRQL = _sbigudrv.CC_GET_IRQL
CC_GET_LINE = _sbigudrv.CC_GET_LINE
CC_GET_LINK_STATUS = _sbigudrv.CC_GET_LINK_STATUS
CC_GET_DRIVER_HANDLE = _sbigudrv.CC_GET_DRIVER_HANDLE
CC_SET_DRIVER_HANDLE = _sbigudrv.CC_SET_DRIVER_HANDLE
CC_START_READOUT = _sbigudrv.CC_START_READOUT
CC_GET_ERROR_STRING = _sbigudrv.CC_GET_ERROR_STRING
CC_SET_DRIVER_CONTROL = _sbigudrv.CC_SET_DRIVER_CONTROL
CC_GET_DRIVER_CONTROL = _sbigudrv.CC_GET_DRIVER_CONTROL
CC_USB_AD_CONTROL = _sbigudrv.CC_USB_AD_CONTROL
CC_QUERY_USB = _sbigudrv.CC_QUERY_USB
CC_GET_PENTIUM_CYCLE_COUNT = _sbigudrv.CC_GET_PENTIUM_CYCLE_COUNT
CC_RW_USB_I2C = _sbigudrv.CC_RW_USB_I2C
CC_CFW = _sbigudrv.CC_CFW
CC_BIT_IO = _sbigudrv.CC_BIT_IO
CC_SEND_BLOCK = _sbigudrv.CC_SEND_BLOCK
CC_SEND_BYTE = _sbigudrv.CC_SEND_BYTE
CC_GET_BYTE = _sbigudrv.CC_GET_BYTE
CC_SEND_AD = _sbigudrv.CC_SEND_AD
CC_GET_AD = _sbigudrv.CC_GET_AD
CC_CLOCK_AD = _sbigudrv.CC_CLOCK_AD
CC_SYSTEM_TEST = _sbigudrv.CC_SYSTEM_TEST
CC_GET_DRIVER_OPTIONS = _sbigudrv.CC_GET_DRIVER_OPTIONS
CC_SET_DRIVER_OPTIONS = _sbigudrv.CC_SET_DRIVER_OPTIONS
CC_LAST_COMMAND = _sbigudrv.CC_LAST_COMMAND
CE_ERROR_BASE = _sbigudrv.CE_ERROR_BASE
CE_NO_ERROR = _sbigudrv.CE_NO_ERROR
CE_CAMERA_NOT_FOUND = _sbigudrv.CE_CAMERA_NOT_FOUND
CE_EXPOSURE_IN_PROGRESS = _sbigudrv.CE_EXPOSURE_IN_PROGRESS
CE_NO_EXPOSURE_IN_PROGRESS = _sbigudrv.CE_NO_EXPOSURE_IN_PROGRESS
CE_UNKNOWN_COMMAND = _sbigudrv.CE_UNKNOWN_COMMAND
CE_BAD_CAMERA_COMMAND = _sbigudrv.CE_BAD_CAMERA_COMMAND
CE_BAD_PARAMETER = _sbigudrv.CE_BAD_PARAMETER
CE_TX_TIMEOUT = _sbigudrv.CE_TX_TIMEOUT
CE_RX_TIMEOUT = _sbigudrv.CE_RX_TIMEOUT
CE_NAK_RECEIVED = _sbigudrv.CE_NAK_RECEIVED
CE_CAN_RECEIVED = _sbigudrv.CE_CAN_RECEIVED
CE_UNKNOWN_RESPONSE = _sbigudrv.CE_UNKNOWN_RESPONSE
CE_BAD_LENGTH = _sbigudrv.CE_BAD_LENGTH
CE_AD_TIMEOUT = _sbigudrv.CE_AD_TIMEOUT
CE_KBD_ESC = _sbigudrv.CE_KBD_ESC
CE_CHECKSUM_ERROR = _sbigudrv.CE_CHECKSUM_ERROR
CE_EEPROM_ERROR = _sbigudrv.CE_EEPROM_ERROR
CE_SHUTTER_ERROR = _sbigudrv.CE_SHUTTER_ERROR
CE_UNKNOWN_CAMERA = _sbigudrv.CE_UNKNOWN_CAMERA
CE_DRIVER_NOT_FOUND = _sbigudrv.CE_DRIVER_NOT_FOUND
CE_DRIVER_NOT_OPEN = _sbigudrv.CE_DRIVER_NOT_OPEN
CE_DRIVER_NOT_CLOSED = _sbigudrv.CE_DRIVER_NOT_CLOSED
CE_SHARE_ERROR = _sbigudrv.CE_SHARE_ERROR
CE_TCE_NOT_FOUND = _sbigudrv.CE_TCE_NOT_FOUND
CE_AO_ERROR = _sbigudrv.CE_AO_ERROR
CE_ECP_ERROR = _sbigudrv.CE_ECP_ERROR
CE_MEMORY_ERROR = _sbigudrv.CE_MEMORY_ERROR
CE_DEVICE_NOT_FOUND = _sbigudrv.CE_DEVICE_NOT_FOUND
CE_DEVICE_NOT_OPEN = _sbigudrv.CE_DEVICE_NOT_OPEN
CE_DEVICE_NOT_CLOSED = _sbigudrv.CE_DEVICE_NOT_CLOSED
CE_DEVICE_NOT_IMPLEMENTED = _sbigudrv.CE_DEVICE_NOT_IMPLEMENTED
CE_DEVICE_DISABLED = _sbigudrv.CE_DEVICE_DISABLED
CE_OS_ERROR = _sbigudrv.CE_OS_ERROR
CE_SOCK_ERROR = _sbigudrv.CE_SOCK_ERROR
CE_SERVER_NOT_FOUND = _sbigudrv.CE_SERVER_NOT_FOUND
CE_CFW_ERROR = _sbigudrv.CE_CFW_ERROR
CE_NEXT_ERROR = _sbigudrv.CE_NEXT_ERROR
CS_IDLE = _sbigudrv.CS_IDLE
CS_IN_PROGRESS = _sbigudrv.CS_IN_PROGRESS
CS_INTEGRATING = _sbigudrv.CS_INTEGRATING
CS_INTEGRATION_COMPLETE = _sbigudrv.CS_INTEGRATION_COMPLETE
CS_PULSE_IN_ACTIVE = _sbigudrv.CS_PULSE_IN_ACTIVE
CS_WAITING_FOR_TRIGGER = _sbigudrv.CS_WAITING_FOR_TRIGGER
ABG_LOW7 = _sbigudrv.ABG_LOW7
ABG_CLK_LOW7 = _sbigudrv.ABG_CLK_LOW7
ABG_CLK_MED7 = _sbigudrv.ABG_CLK_MED7
ABG_CLK_HI7 = _sbigudrv.ABG_CLK_HI7
FALSE = _sbigudrv.FALSE
TRUE = _sbigudrv.TRUE
DRIVER_STD = _sbigudrv.DRIVER_STD
DRIVER_EXTENDED = _sbigudrv.DRIVER_EXTENDED
DRIVER_USB_LOADER = _sbigudrv.DRIVER_USB_LOADER
CCD_IMAGING = _sbigudrv.CCD_IMAGING
CCD_TRACKING = _sbigudrv.CCD_TRACKING
CCD_EXT_TRACKING = _sbigudrv.CCD_EXT_TRACKING
CCD_INFO_IMAGING = _sbigudrv.CCD_INFO_IMAGING
CCD_INFO_TRACKING = _sbigudrv.CCD_INFO_TRACKING
CCD_INFO_EXTENDED = _sbigudrv.CCD_INFO_EXTENDED
CCD_INFO_EXTENDED_5C = _sbigudrv.CCD_INFO_EXTENDED_5C
CCD_INFO_EXTENDED2_IMAGING = _sbigudrv.CCD_INFO_EXTENDED2_IMAGING
CCD_INFO_EXTENDED2_TRACKING = _sbigudrv.CCD_INFO_EXTENDED2_TRACKING
ABG_NOT_PRESENT = _sbigudrv.ABG_NOT_PRESENT
ABG_PRESENT = _sbigudrv.ABG_PRESENT
BR_AUTO = _sbigudrv.BR_AUTO
BR_9600 = _sbigudrv.BR_9600
BR_19K = _sbigudrv.BR_19K
BR_38K = _sbigudrv.BR_38K
BR_57K = _sbigudrv.BR_57K
BR_115K = _sbigudrv.BR_115K
ST7_CAMERA = _sbigudrv.ST7_CAMERA
ST8_CAMERA = _sbigudrv.ST8_CAMERA
ST5C_CAMERA = _sbigudrv.ST5C_CAMERA
TCE_CONTROLLER = _sbigudrv.TCE_CONTROLLER
ST237_CAMERA = _sbigudrv.ST237_CAMERA
STK_CAMERA = _sbigudrv.STK_CAMERA
ST9_CAMERA = _sbigudrv.ST9_CAMERA
STV_CAMERA = _sbigudrv.STV_CAMERA
ST10_CAMERA = _sbigudrv.ST10_CAMERA
ST1K_CAMERA = _sbigudrv.ST1K_CAMERA
ST2K_CAMERA = _sbigudrv.ST2K_CAMERA
STL_CAMERA = _sbigudrv.STL_CAMERA
ST402_CAMERA = _sbigudrv.ST402_CAMERA
NEXT_CAMERA = _sbigudrv.NEXT_CAMERA
NO_CAMERA = _sbigudrv.NO_CAMERA
SC_LEAVE_SHUTTER = _sbigudrv.SC_LEAVE_SHUTTER
SC_OPEN_SHUTTER = _sbigudrv.SC_OPEN_SHUTTER
SC_CLOSE_SHUTTER = _sbigudrv.SC_CLOSE_SHUTTER
SC_INITIALIZE_SHUTTER = _sbigudrv.SC_INITIALIZE_SHUTTER
SC_OPEN_EXT_SHUTTER = _sbigudrv.SC_OPEN_EXT_SHUTTER
SC_CLOSE_EXT_SHUTTER = _sbigudrv.SC_CLOSE_EXT_SHUTTER
SS_OPEN = _sbigudrv.SS_OPEN
SS_CLOSED = _sbigudrv.SS_CLOSED
SS_OPENING = _sbigudrv.SS_OPENING
SS_CLOSING = _sbigudrv.SS_CLOSING
REGULATION_OFF = _sbigudrv.REGULATION_OFF
REGULATION_ON = _sbigudrv.REGULATION_ON
REGULATION_OVERRIDE = _sbigudrv.REGULATION_OVERRIDE
REGULATION_FREEZE = _sbigudrv.REGULATION_FREEZE
REGULATION_UNFREEZE = _sbigudrv.REGULATION_UNFREEZE
REGULATION_ENABLE_AUTOFREEZE = _sbigudrv.REGULATION_ENABLE_AUTOFREEZE
REGULATION_DISABLE_AUTOFREEZE = _sbigudrv.REGULATION_DISABLE_AUTOFREEZE
REGULATION_FROZEN_MASK = _sbigudrv.REGULATION_FROZEN_MASK
LED_OFF = _sbigudrv.LED_OFF
LED_ON = _sbigudrv.LED_ON
LED_BLINK_LOW = _sbigudrv.LED_BLINK_LOW
LED_BLINK_HIGH = _sbigudrv.LED_BLINK_HIGH
FILTER_LEAVE = _sbigudrv.FILTER_LEAVE
FILTER_SET_1 = _sbigudrv.FILTER_SET_1
FILTER_SET_2 = _sbigudrv.FILTER_SET_2
FILTER_SET_3 = _sbigudrv.FILTER_SET_3
FILTER_SET_4 = _sbigudrv.FILTER_SET_4
FILTER_SET_5 = _sbigudrv.FILTER_SET_5
FILTER_STOP = _sbigudrv.FILTER_STOP
FILTER_INIT = _sbigudrv.FILTER_INIT
FS_MOVING = _sbigudrv.FS_MOVING
FS_AT_1 = _sbigudrv.FS_AT_1
FS_AT_2 = _sbigudrv.FS_AT_2
FS_AT_3 = _sbigudrv.FS_AT_3
FS_AT_4 = _sbigudrv.FS_AT_4
FS_AT_5 = _sbigudrv.FS_AT_5
FS_UNKNOWN = _sbigudrv.FS_UNKNOWN
AD_UNKNOWN = _sbigudrv.AD_UNKNOWN
AD_12_BITS = _sbigudrv.AD_12_BITS
AD_16_BITS = _sbigudrv.AD_16_BITS
FW_UNKNOWN = _sbigudrv.FW_UNKNOWN
FW_EXTERNAL = _sbigudrv.FW_EXTERNAL
FW_VANE = _sbigudrv.FW_VANE
FW_FILTER_WHEEL = _sbigudrv.FW_FILTER_WHEEL
AOF_HARD_CENTER = _sbigudrv.AOF_HARD_CENTER
AOF_SOFT_CENTER = _sbigudrv.AOF_SOFT_CENTER
AOF_STEP_IN = _sbigudrv.AOF_STEP_IN
AOF_STEP_OUT = _sbigudrv.AOF_STEP_OUT
DEV_NONE = _sbigudrv.DEV_NONE
DEV_LPT1 = _sbigudrv.DEV_LPT1
DEV_LPT2 = _sbigudrv.DEV_LPT2
DEV_LPT3 = _sbigudrv.DEV_LPT3
DEV_USB = _sbigudrv.DEV_USB
DEV_ETH = _sbigudrv.DEV_ETH
DEV_USB1 = _sbigudrv.DEV_USB1
DEV_USB2 = _sbigudrv.DEV_USB2
DEV_USB3 = _sbigudrv.DEV_USB3
DEV_USB4 = _sbigudrv.DEV_USB4
DCP_USB_FIFO_ENABLE = _sbigudrv.DCP_USB_FIFO_ENABLE
DCP_CALL_JOURNAL_ENABLE = _sbigudrv.DCP_CALL_JOURNAL_ENABLE
DCP_IVTOH_RATIO = _sbigudrv.DCP_IVTOH_RATIO
DCP_USB_FIFO_SIZE = _sbigudrv.DCP_USB_FIFO_SIZE
DCP_USB_DRIVER = _sbigudrv.DCP_USB_DRIVER
DCP_KAI_RELGAIN = _sbigudrv.DCP_KAI_RELGAIN
DCP_USB_PIXEL_DL_ENABLE = _sbigudrv.DCP_USB_PIXEL_DL_ENABLE
DCP_HIGH_THROUGHPUT = _sbigudrv.DCP_HIGH_THROUGHPUT
DCP_VDD_OPTIMIZED = _sbigudrv.DCP_VDD_OPTIMIZED
DCP_AUTO_AD_GAIN = _sbigudrv.DCP_AUTO_AD_GAIN
DCP_LAST = _sbigudrv.DCP_LAST
USB_AD_IMAGING_GAIN = _sbigudrv.USB_AD_IMAGING_GAIN
USB_AD_IMAGING_OFFSET = _sbigudrv.USB_AD_IMAGING_OFFSET
USB_AD_TRACKING_GAIN = _sbigudrv.USB_AD_TRACKING_GAIN
USB_AD_TRACKING_OFFSET = _sbigudrv.USB_AD_TRACKING_OFFSET
USBD_SBIGE = _sbigudrv.USBD_SBIGE
USBD_SBIGI = _sbigudrv.USBD_SBIGI
USBD_SBIGM = _sbigudrv.USBD_SBIGM
USBD_NEXT = _sbigudrv.USBD_NEXT
CFWSEL_UNKNOWN = _sbigudrv.CFWSEL_UNKNOWN
CFWSEL_CFW2 = _sbigudrv.CFWSEL_CFW2
CFWSEL_CFW5 = _sbigudrv.CFWSEL_CFW5
CFWSEL_CFW8 = _sbigudrv.CFWSEL_CFW8
CFWSEL_CFWL = _sbigudrv.CFWSEL_CFWL
CFWSEL_CFW402 = _sbigudrv.CFWSEL_CFW402
CFWSEL_AUTO = _sbigudrv.CFWSEL_AUTO
CFWSEL_CFW6A = _sbigudrv.CFWSEL_CFW6A
CFWSEL_CFW10 = _sbigudrv.CFWSEL_CFW10
CFWSEL_CFW10_SERIAL = _sbigudrv.CFWSEL_CFW10_SERIAL
CFWC_QUERY = _sbigudrv.CFWC_QUERY
CFWC_GOTO = _sbigudrv.CFWC_GOTO
CFWC_INIT = _sbigudrv.CFWC_INIT
CFWC_GET_INFO = _sbigudrv.CFWC_GET_INFO
CFWC_OPEN_DEVICE = _sbigudrv.CFWC_OPEN_DEVICE
CFWC_CLOSE_DEVICE = _sbigudrv.CFWC_CLOSE_DEVICE
CFWS_UNKNOWN = _sbigudrv.CFWS_UNKNOWN
CFWS_IDLE = _sbigudrv.CFWS_IDLE
CFWS_BUSY = _sbigudrv.CFWS_BUSY
CFWE_NONE = _sbigudrv.CFWE_NONE
CFWE_BUSY = _sbigudrv.CFWE_BUSY
CFWE_BAD_COMMAND = _sbigudrv.CFWE_BAD_COMMAND
CFWE_CAL_ERROR = _sbigudrv.CFWE_CAL_ERROR
CFWE_MOTOR_TIMEOUT = _sbigudrv.CFWE_MOTOR_TIMEOUT
CFWE_BAD_MODEL = _sbigudrv.CFWE_BAD_MODEL
CFWE_DEVICE_NOT_CLOSED = _sbigudrv.CFWE_DEVICE_NOT_CLOSED
CFWE_DEVICE_NOT_OPEN = _sbigudrv.CFWE_DEVICE_NOT_OPEN
CFWE_I2C_ERROR = _sbigudrv.CFWE_I2C_ERROR
CFWP_UNKNOWN = _sbigudrv.CFWP_UNKNOWN
CFWP_1 = _sbigudrv.CFWP_1
CFWP_2 = _sbigudrv.CFWP_2
CFWP_3 = _sbigudrv.CFWP_3
CFWP_4 = _sbigudrv.CFWP_4
CFWP_5 = _sbigudrv.CFWP_5
CFWP_6 = _sbigudrv.CFWP_6
CFWP_7 = _sbigudrv.CFWP_7
CFWP_8 = _sbigudrv.CFWP_8
CFWP_9 = _sbigudrv.CFWP_9
CFWP_10 = _sbigudrv.CFWP_10
CFWPORT_COM1 = _sbigudrv.CFWPORT_COM1
CFWPORT_COM2 = _sbigudrv.CFWPORT_COM2
CFWPORT_COM3 = _sbigudrv.CFWPORT_COM3
CFWPORT_COM4 = _sbigudrv.CFWPORT_COM4
CFWG_FIRMWARE_VERSION = _sbigudrv.CFWG_FIRMWARE_VERSION
CFWG_CAL_DATA = _sbigudrv.CFWG_CAL_DATA
CFWG_DATA_REGISTERS = _sbigudrv.CFWG_DATA_REGISTERS
BITIO_WRITE = _sbigudrv.BITIO_WRITE
BITIO_READ = _sbigudrv.BITIO_READ
BITI_PS_LOW = _sbigudrv.BITI_PS_LOW
BITO_IO1 = _sbigudrv.BITO_IO1
BITO_IO2 = _sbigudrv.BITO_IO2
BITI_IO3 = _sbigudrv.BITI_IO3
BITO_FPGA_WE = _sbigudrv.BITO_FPGA_WE
END_SKIP_DELAY = _sbigudrv.END_SKIP_DELAY
START_SKIP_VDD = _sbigudrv.START_SKIP_VDD
START_MOTOR_ALWAYS_ON = _sbigudrv.START_MOTOR_ALWAYS_ON
EXP_WAIT_FOR_TRIGGER_IN = _sbigudrv.EXP_WAIT_FOR_TRIGGER_IN
EXP_SEND_TRIGGER_OUT = _sbigudrv.EXP_SEND_TRIGGER_OUT
EXP_LIGHT_CLEAR = _sbigudrv.EXP_LIGHT_CLEAR
EXP_MS_EXPOSURE = _sbigudrv.EXP_MS_EXPOSURE
EXP_TIME_MASK = _sbigudrv.EXP_TIME_MASK
CB_CCD_TYPE_MASK = _sbigudrv.CB_CCD_TYPE_MASK
CB_CCD_TYPE_FULL_FRAME = _sbigudrv.CB_CCD_TYPE_FULL_FRAME
CB_CCD_TYPE_FRAME_TRANSFER = _sbigudrv.CB_CCD_TYPE_FRAME_TRANSFER
CB_CCD_ESHUTTER_MASK = _sbigudrv.CB_CCD_ESHUTTER_MASK
CB_CCD_ESHUTTER_NO = _sbigudrv.CB_CCD_ESHUTTER_NO
CB_CCD_ESHUTTER_YES = _sbigudrv.CB_CCD_ESHUTTER_YES
MIN_ST7_EXPOSURE = _sbigudrv.MIN_ST7_EXPOSURE
MIN_ST402_EXPOSURE = _sbigudrv.MIN_ST402_EXPOSURE
MIN_ST3200_EXPOSURE = _sbigudrv.MIN_ST3200_EXPOSURE
class StartExposureParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, StartExposureParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, StartExposureParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.StartExposureParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.StartExposureParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.StartExposureParams_ccd_get, _sbigudrv.StartExposureParams_ccd_set)
    __swig_setmethods__["exposureTime"] = _sbigudrv.StartExposureParams_exposureTime_set
    __swig_getmethods__["exposureTime"] = _sbigudrv.StartExposureParams_exposureTime_get
    if _newclass:exposureTime = property(_sbigudrv.StartExposureParams_exposureTime_get, _sbigudrv.StartExposureParams_exposureTime_set)
    __swig_setmethods__["abgState"] = _sbigudrv.StartExposureParams_abgState_set
    __swig_getmethods__["abgState"] = _sbigudrv.StartExposureParams_abgState_get
    if _newclass:abgState = property(_sbigudrv.StartExposureParams_abgState_get, _sbigudrv.StartExposureParams_abgState_set)
    __swig_setmethods__["openShutter"] = _sbigudrv.StartExposureParams_openShutter_set
    __swig_getmethods__["openShutter"] = _sbigudrv.StartExposureParams_openShutter_get
    if _newclass:openShutter = property(_sbigudrv.StartExposureParams_openShutter_get, _sbigudrv.StartExposureParams_openShutter_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_StartExposureParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_StartExposureParams
    __del__ = lambda self : None;
StartExposureParams_swigregister = _sbigudrv.StartExposureParams_swigregister
StartExposureParams_swigregister(StartExposureParams)

class EndExposureParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, EndExposureParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, EndExposureParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.EndExposureParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.EndExposureParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.EndExposureParams_ccd_get, _sbigudrv.EndExposureParams_ccd_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_EndExposureParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_EndExposureParams
    __del__ = lambda self : None;
EndExposureParams_swigregister = _sbigudrv.EndExposureParams_swigregister
EndExposureParams_swigregister(EndExposureParams)

class ReadoutLineParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ReadoutLineParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ReadoutLineParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.ReadoutLineParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.ReadoutLineParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.ReadoutLineParams_ccd_get, _sbigudrv.ReadoutLineParams_ccd_set)
    __swig_setmethods__["readoutMode"] = _sbigudrv.ReadoutLineParams_readoutMode_set
    __swig_getmethods__["readoutMode"] = _sbigudrv.ReadoutLineParams_readoutMode_get
    if _newclass:readoutMode = property(_sbigudrv.ReadoutLineParams_readoutMode_get, _sbigudrv.ReadoutLineParams_readoutMode_set)
    __swig_setmethods__["pixelStart"] = _sbigudrv.ReadoutLineParams_pixelStart_set
    __swig_getmethods__["pixelStart"] = _sbigudrv.ReadoutLineParams_pixelStart_get
    if _newclass:pixelStart = property(_sbigudrv.ReadoutLineParams_pixelStart_get, _sbigudrv.ReadoutLineParams_pixelStart_set)
    __swig_setmethods__["pixelLength"] = _sbigudrv.ReadoutLineParams_pixelLength_set
    __swig_getmethods__["pixelLength"] = _sbigudrv.ReadoutLineParams_pixelLength_get
    if _newclass:pixelLength = property(_sbigudrv.ReadoutLineParams_pixelLength_get, _sbigudrv.ReadoutLineParams_pixelLength_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_ReadoutLineParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_ReadoutLineParams
    __del__ = lambda self : None;
ReadoutLineParams_swigregister = _sbigudrv.ReadoutLineParams_swigregister
ReadoutLineParams_swigregister(ReadoutLineParams)

class DumpLinesParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, DumpLinesParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, DumpLinesParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.DumpLinesParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.DumpLinesParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.DumpLinesParams_ccd_get, _sbigudrv.DumpLinesParams_ccd_set)
    __swig_setmethods__["readoutMode"] = _sbigudrv.DumpLinesParams_readoutMode_set
    __swig_getmethods__["readoutMode"] = _sbigudrv.DumpLinesParams_readoutMode_get
    if _newclass:readoutMode = property(_sbigudrv.DumpLinesParams_readoutMode_get, _sbigudrv.DumpLinesParams_readoutMode_set)
    __swig_setmethods__["lineLength"] = _sbigudrv.DumpLinesParams_lineLength_set
    __swig_getmethods__["lineLength"] = _sbigudrv.DumpLinesParams_lineLength_get
    if _newclass:lineLength = property(_sbigudrv.DumpLinesParams_lineLength_get, _sbigudrv.DumpLinesParams_lineLength_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_DumpLinesParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_DumpLinesParams
    __del__ = lambda self : None;
DumpLinesParams_swigregister = _sbigudrv.DumpLinesParams_swigregister
DumpLinesParams_swigregister(DumpLinesParams)

class EndReadoutParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, EndReadoutParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, EndReadoutParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.EndReadoutParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.EndReadoutParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.EndReadoutParams_ccd_get, _sbigudrv.EndReadoutParams_ccd_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_EndReadoutParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_EndReadoutParams
    __del__ = lambda self : None;
EndReadoutParams_swigregister = _sbigudrv.EndReadoutParams_swigregister
EndReadoutParams_swigregister(EndReadoutParams)

class StartReadoutParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, StartReadoutParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, StartReadoutParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.StartReadoutParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.StartReadoutParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.StartReadoutParams_ccd_get, _sbigudrv.StartReadoutParams_ccd_set)
    __swig_setmethods__["readoutMode"] = _sbigudrv.StartReadoutParams_readoutMode_set
    __swig_getmethods__["readoutMode"] = _sbigudrv.StartReadoutParams_readoutMode_get
    if _newclass:readoutMode = property(_sbigudrv.StartReadoutParams_readoutMode_get, _sbigudrv.StartReadoutParams_readoutMode_set)
    __swig_setmethods__["top"] = _sbigudrv.StartReadoutParams_top_set
    __swig_getmethods__["top"] = _sbigudrv.StartReadoutParams_top_get
    if _newclass:top = property(_sbigudrv.StartReadoutParams_top_get, _sbigudrv.StartReadoutParams_top_set)
    __swig_setmethods__["left"] = _sbigudrv.StartReadoutParams_left_set
    __swig_getmethods__["left"] = _sbigudrv.StartReadoutParams_left_get
    if _newclass:left = property(_sbigudrv.StartReadoutParams_left_get, _sbigudrv.StartReadoutParams_left_set)
    __swig_setmethods__["height"] = _sbigudrv.StartReadoutParams_height_set
    __swig_getmethods__["height"] = _sbigudrv.StartReadoutParams_height_get
    if _newclass:height = property(_sbigudrv.StartReadoutParams_height_get, _sbigudrv.StartReadoutParams_height_set)
    __swig_setmethods__["width"] = _sbigudrv.StartReadoutParams_width_set
    __swig_getmethods__["width"] = _sbigudrv.StartReadoutParams_width_get
    if _newclass:width = property(_sbigudrv.StartReadoutParams_width_get, _sbigudrv.StartReadoutParams_width_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_StartReadoutParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_StartReadoutParams
    __del__ = lambda self : None;
StartReadoutParams_swigregister = _sbigudrv.StartReadoutParams_swigregister
StartReadoutParams_swigregister(StartReadoutParams)

class SetTemperatureRegulationParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SetTemperatureRegulationParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SetTemperatureRegulationParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["regulation"] = _sbigudrv.SetTemperatureRegulationParams_regulation_set
    __swig_getmethods__["regulation"] = _sbigudrv.SetTemperatureRegulationParams_regulation_get
    if _newclass:regulation = property(_sbigudrv.SetTemperatureRegulationParams_regulation_get, _sbigudrv.SetTemperatureRegulationParams_regulation_set)
    __swig_setmethods__["ccdSetpoint"] = _sbigudrv.SetTemperatureRegulationParams_ccdSetpoint_set
    __swig_getmethods__["ccdSetpoint"] = _sbigudrv.SetTemperatureRegulationParams_ccdSetpoint_get
    if _newclass:ccdSetpoint = property(_sbigudrv.SetTemperatureRegulationParams_ccdSetpoint_get, _sbigudrv.SetTemperatureRegulationParams_ccdSetpoint_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SetTemperatureRegulationParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SetTemperatureRegulationParams
    __del__ = lambda self : None;
SetTemperatureRegulationParams_swigregister = _sbigudrv.SetTemperatureRegulationParams_swigregister
SetTemperatureRegulationParams_swigregister(SetTemperatureRegulationParams)

class QueryTemperatureStatusResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, QueryTemperatureStatusResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, QueryTemperatureStatusResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["enabled"] = _sbigudrv.QueryTemperatureStatusResults_enabled_set
    __swig_getmethods__["enabled"] = _sbigudrv.QueryTemperatureStatusResults_enabled_get
    if _newclass:enabled = property(_sbigudrv.QueryTemperatureStatusResults_enabled_get, _sbigudrv.QueryTemperatureStatusResults_enabled_set)
    __swig_setmethods__["ccdSetpoint"] = _sbigudrv.QueryTemperatureStatusResults_ccdSetpoint_set
    __swig_getmethods__["ccdSetpoint"] = _sbigudrv.QueryTemperatureStatusResults_ccdSetpoint_get
    if _newclass:ccdSetpoint = property(_sbigudrv.QueryTemperatureStatusResults_ccdSetpoint_get, _sbigudrv.QueryTemperatureStatusResults_ccdSetpoint_set)
    __swig_setmethods__["power"] = _sbigudrv.QueryTemperatureStatusResults_power_set
    __swig_getmethods__["power"] = _sbigudrv.QueryTemperatureStatusResults_power_get
    if _newclass:power = property(_sbigudrv.QueryTemperatureStatusResults_power_get, _sbigudrv.QueryTemperatureStatusResults_power_set)
    __swig_setmethods__["ccdThermistor"] = _sbigudrv.QueryTemperatureStatusResults_ccdThermistor_set
    __swig_getmethods__["ccdThermistor"] = _sbigudrv.QueryTemperatureStatusResults_ccdThermistor_get
    if _newclass:ccdThermistor = property(_sbigudrv.QueryTemperatureStatusResults_ccdThermistor_get, _sbigudrv.QueryTemperatureStatusResults_ccdThermistor_set)
    __swig_setmethods__["ambientThermistor"] = _sbigudrv.QueryTemperatureStatusResults_ambientThermistor_set
    __swig_getmethods__["ambientThermistor"] = _sbigudrv.QueryTemperatureStatusResults_ambientThermistor_get
    if _newclass:ambientThermistor = property(_sbigudrv.QueryTemperatureStatusResults_ambientThermistor_get, _sbigudrv.QueryTemperatureStatusResults_ambientThermistor_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_QueryTemperatureStatusResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_QueryTemperatureStatusResults
    __del__ = lambda self : None;
QueryTemperatureStatusResults_swigregister = _sbigudrv.QueryTemperatureStatusResults_swigregister
QueryTemperatureStatusResults_swigregister(QueryTemperatureStatusResults)

class ActivateRelayParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ActivateRelayParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ActivateRelayParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["tXPlus"] = _sbigudrv.ActivateRelayParams_tXPlus_set
    __swig_getmethods__["tXPlus"] = _sbigudrv.ActivateRelayParams_tXPlus_get
    if _newclass:tXPlus = property(_sbigudrv.ActivateRelayParams_tXPlus_get, _sbigudrv.ActivateRelayParams_tXPlus_set)
    __swig_setmethods__["tXMinus"] = _sbigudrv.ActivateRelayParams_tXMinus_set
    __swig_getmethods__["tXMinus"] = _sbigudrv.ActivateRelayParams_tXMinus_get
    if _newclass:tXMinus = property(_sbigudrv.ActivateRelayParams_tXMinus_get, _sbigudrv.ActivateRelayParams_tXMinus_set)
    __swig_setmethods__["tYPlus"] = _sbigudrv.ActivateRelayParams_tYPlus_set
    __swig_getmethods__["tYPlus"] = _sbigudrv.ActivateRelayParams_tYPlus_get
    if _newclass:tYPlus = property(_sbigudrv.ActivateRelayParams_tYPlus_get, _sbigudrv.ActivateRelayParams_tYPlus_set)
    __swig_setmethods__["tYMinus"] = _sbigudrv.ActivateRelayParams_tYMinus_set
    __swig_getmethods__["tYMinus"] = _sbigudrv.ActivateRelayParams_tYMinus_get
    if _newclass:tYMinus = property(_sbigudrv.ActivateRelayParams_tYMinus_get, _sbigudrv.ActivateRelayParams_tYMinus_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_ActivateRelayParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_ActivateRelayParams
    __del__ = lambda self : None;
ActivateRelayParams_swigregister = _sbigudrv.ActivateRelayParams_swigregister
ActivateRelayParams_swigregister(ActivateRelayParams)

class PulseOutParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, PulseOutParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, PulseOutParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["numberPulses"] = _sbigudrv.PulseOutParams_numberPulses_set
    __swig_getmethods__["numberPulses"] = _sbigudrv.PulseOutParams_numberPulses_get
    if _newclass:numberPulses = property(_sbigudrv.PulseOutParams_numberPulses_get, _sbigudrv.PulseOutParams_numberPulses_set)
    __swig_setmethods__["pulseWidth"] = _sbigudrv.PulseOutParams_pulseWidth_set
    __swig_getmethods__["pulseWidth"] = _sbigudrv.PulseOutParams_pulseWidth_get
    if _newclass:pulseWidth = property(_sbigudrv.PulseOutParams_pulseWidth_get, _sbigudrv.PulseOutParams_pulseWidth_set)
    __swig_setmethods__["pulsePeriod"] = _sbigudrv.PulseOutParams_pulsePeriod_set
    __swig_getmethods__["pulsePeriod"] = _sbigudrv.PulseOutParams_pulsePeriod_get
    if _newclass:pulsePeriod = property(_sbigudrv.PulseOutParams_pulsePeriod_get, _sbigudrv.PulseOutParams_pulsePeriod_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_PulseOutParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_PulseOutParams
    __del__ = lambda self : None;
PulseOutParams_swigregister = _sbigudrv.PulseOutParams_swigregister
PulseOutParams_swigregister(PulseOutParams)

class TXSerialBytesParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TXSerialBytesParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TXSerialBytesParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["dataLength"] = _sbigudrv.TXSerialBytesParams_dataLength_set
    __swig_getmethods__["dataLength"] = _sbigudrv.TXSerialBytesParams_dataLength_get
    if _newclass:dataLength = property(_sbigudrv.TXSerialBytesParams_dataLength_get, _sbigudrv.TXSerialBytesParams_dataLength_set)
    __swig_setmethods__["data"] = _sbigudrv.TXSerialBytesParams_data_set
    __swig_getmethods__["data"] = _sbigudrv.TXSerialBytesParams_data_get
    if _newclass:data = property(_sbigudrv.TXSerialBytesParams_data_get, _sbigudrv.TXSerialBytesParams_data_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_TXSerialBytesParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_TXSerialBytesParams
    __del__ = lambda self : None;
TXSerialBytesParams_swigregister = _sbigudrv.TXSerialBytesParams_swigregister
TXSerialBytesParams_swigregister(TXSerialBytesParams)

class TXSerialBytesResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, TXSerialBytesResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, TXSerialBytesResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["bytesSent"] = _sbigudrv.TXSerialBytesResults_bytesSent_set
    __swig_getmethods__["bytesSent"] = _sbigudrv.TXSerialBytesResults_bytesSent_get
    if _newclass:bytesSent = property(_sbigudrv.TXSerialBytesResults_bytesSent_get, _sbigudrv.TXSerialBytesResults_bytesSent_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_TXSerialBytesResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_TXSerialBytesResults
    __del__ = lambda self : None;
TXSerialBytesResults_swigregister = _sbigudrv.TXSerialBytesResults_swigregister
TXSerialBytesResults_swigregister(TXSerialBytesResults)

class GetSerialStatusResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetSerialStatusResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetSerialStatusResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["clearToCOM"] = _sbigudrv.GetSerialStatusResults_clearToCOM_set
    __swig_getmethods__["clearToCOM"] = _sbigudrv.GetSerialStatusResults_clearToCOM_get
    if _newclass:clearToCOM = property(_sbigudrv.GetSerialStatusResults_clearToCOM_get, _sbigudrv.GetSerialStatusResults_clearToCOM_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetSerialStatusResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetSerialStatusResults
    __del__ = lambda self : None;
GetSerialStatusResults_swigregister = _sbigudrv.GetSerialStatusResults_swigregister
GetSerialStatusResults_swigregister(GetSerialStatusResults)

class EstablishLinkParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, EstablishLinkParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, EstablishLinkParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["sbigUseOnly"] = _sbigudrv.EstablishLinkParams_sbigUseOnly_set
    __swig_getmethods__["sbigUseOnly"] = _sbigudrv.EstablishLinkParams_sbigUseOnly_get
    if _newclass:sbigUseOnly = property(_sbigudrv.EstablishLinkParams_sbigUseOnly_get, _sbigudrv.EstablishLinkParams_sbigUseOnly_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_EstablishLinkParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_EstablishLinkParams
    __del__ = lambda self : None;
EstablishLinkParams_swigregister = _sbigudrv.EstablishLinkParams_swigregister
EstablishLinkParams_swigregister(EstablishLinkParams)

class EstablishLinkResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, EstablishLinkResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, EstablishLinkResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["cameraType"] = _sbigudrv.EstablishLinkResults_cameraType_set
    __swig_getmethods__["cameraType"] = _sbigudrv.EstablishLinkResults_cameraType_get
    if _newclass:cameraType = property(_sbigudrv.EstablishLinkResults_cameraType_get, _sbigudrv.EstablishLinkResults_cameraType_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_EstablishLinkResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_EstablishLinkResults
    __del__ = lambda self : None;
EstablishLinkResults_swigregister = _sbigudrv.EstablishLinkResults_swigregister
EstablishLinkResults_swigregister(EstablishLinkResults)

class GetDriverInfoParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetDriverInfoParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetDriverInfoParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["request"] = _sbigudrv.GetDriverInfoParams_request_set
    __swig_getmethods__["request"] = _sbigudrv.GetDriverInfoParams_request_get
    if _newclass:request = property(_sbigudrv.GetDriverInfoParams_request_get, _sbigudrv.GetDriverInfoParams_request_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetDriverInfoParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetDriverInfoParams
    __del__ = lambda self : None;
GetDriverInfoParams_swigregister = _sbigudrv.GetDriverInfoParams_swigregister
GetDriverInfoParams_swigregister(GetDriverInfoParams)

class GetDriverInfoResults0(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetDriverInfoResults0, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetDriverInfoResults0, name)
    __repr__ = _swig_repr
    __swig_setmethods__["version"] = _sbigudrv.GetDriverInfoResults0_version_set
    __swig_getmethods__["version"] = _sbigudrv.GetDriverInfoResults0_version_get
    if _newclass:version = property(_sbigudrv.GetDriverInfoResults0_version_get, _sbigudrv.GetDriverInfoResults0_version_set)
    __swig_setmethods__["name"] = _sbigudrv.GetDriverInfoResults0_name_set
    __swig_getmethods__["name"] = _sbigudrv.GetDriverInfoResults0_name_get
    if _newclass:name = property(_sbigudrv.GetDriverInfoResults0_name_get, _sbigudrv.GetDriverInfoResults0_name_set)
    __swig_setmethods__["maxRequest"] = _sbigudrv.GetDriverInfoResults0_maxRequest_set
    __swig_getmethods__["maxRequest"] = _sbigudrv.GetDriverInfoResults0_maxRequest_get
    if _newclass:maxRequest = property(_sbigudrv.GetDriverInfoResults0_maxRequest_get, _sbigudrv.GetDriverInfoResults0_maxRequest_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetDriverInfoResults0(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetDriverInfoResults0
    __del__ = lambda self : None;
GetDriverInfoResults0_swigregister = _sbigudrv.GetDriverInfoResults0_swigregister
GetDriverInfoResults0_swigregister(GetDriverInfoResults0)

class GetCCDInfoParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetCCDInfoParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetCCDInfoParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["request"] = _sbigudrv.GetCCDInfoParams_request_set
    __swig_getmethods__["request"] = _sbigudrv.GetCCDInfoParams_request_get
    if _newclass:request = property(_sbigudrv.GetCCDInfoParams_request_get, _sbigudrv.GetCCDInfoParams_request_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetCCDInfoParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetCCDInfoParams
    __del__ = lambda self : None;
GetCCDInfoParams_swigregister = _sbigudrv.GetCCDInfoParams_swigregister
GetCCDInfoParams_swigregister(GetCCDInfoParams)

class READOUT_INFO(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, READOUT_INFO, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, READOUT_INFO, name)
    __repr__ = _swig_repr
    __swig_setmethods__["mode"] = _sbigudrv.READOUT_INFO_mode_set
    __swig_getmethods__["mode"] = _sbigudrv.READOUT_INFO_mode_get
    if _newclass:mode = property(_sbigudrv.READOUT_INFO_mode_get, _sbigudrv.READOUT_INFO_mode_set)
    __swig_setmethods__["width"] = _sbigudrv.READOUT_INFO_width_set
    __swig_getmethods__["width"] = _sbigudrv.READOUT_INFO_width_get
    if _newclass:width = property(_sbigudrv.READOUT_INFO_width_get, _sbigudrv.READOUT_INFO_width_set)
    __swig_setmethods__["height"] = _sbigudrv.READOUT_INFO_height_set
    __swig_getmethods__["height"] = _sbigudrv.READOUT_INFO_height_get
    if _newclass:height = property(_sbigudrv.READOUT_INFO_height_get, _sbigudrv.READOUT_INFO_height_set)
    __swig_setmethods__["gain"] = _sbigudrv.READOUT_INFO_gain_set
    __swig_getmethods__["gain"] = _sbigudrv.READOUT_INFO_gain_get
    if _newclass:gain = property(_sbigudrv.READOUT_INFO_gain_get, _sbigudrv.READOUT_INFO_gain_set)
    __swig_setmethods__["pixel_width"] = _sbigudrv.READOUT_INFO_pixel_width_set
    __swig_getmethods__["pixel_width"] = _sbigudrv.READOUT_INFO_pixel_width_get
    if _newclass:pixel_width = property(_sbigudrv.READOUT_INFO_pixel_width_get, _sbigudrv.READOUT_INFO_pixel_width_set)
    __swig_setmethods__["pixel_height"] = _sbigudrv.READOUT_INFO_pixel_height_set
    __swig_getmethods__["pixel_height"] = _sbigudrv.READOUT_INFO_pixel_height_get
    if _newclass:pixel_height = property(_sbigudrv.READOUT_INFO_pixel_height_get, _sbigudrv.READOUT_INFO_pixel_height_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_READOUT_INFO(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_READOUT_INFO
    __del__ = lambda self : None;
READOUT_INFO_swigregister = _sbigudrv.READOUT_INFO_swigregister
READOUT_INFO_swigregister(READOUT_INFO)

class GetCCDInfoResults0(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetCCDInfoResults0, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetCCDInfoResults0, name)
    __repr__ = _swig_repr
    __swig_setmethods__["firmwareVersion"] = _sbigudrv.GetCCDInfoResults0_firmwareVersion_set
    __swig_getmethods__["firmwareVersion"] = _sbigudrv.GetCCDInfoResults0_firmwareVersion_get
    if _newclass:firmwareVersion = property(_sbigudrv.GetCCDInfoResults0_firmwareVersion_get, _sbigudrv.GetCCDInfoResults0_firmwareVersion_set)
    __swig_setmethods__["cameraType"] = _sbigudrv.GetCCDInfoResults0_cameraType_set
    __swig_getmethods__["cameraType"] = _sbigudrv.GetCCDInfoResults0_cameraType_get
    if _newclass:cameraType = property(_sbigudrv.GetCCDInfoResults0_cameraType_get, _sbigudrv.GetCCDInfoResults0_cameraType_set)
    __swig_setmethods__["name"] = _sbigudrv.GetCCDInfoResults0_name_set
    __swig_getmethods__["name"] = _sbigudrv.GetCCDInfoResults0_name_get
    if _newclass:name = property(_sbigudrv.GetCCDInfoResults0_name_get, _sbigudrv.GetCCDInfoResults0_name_set)
    __swig_setmethods__["readoutModes"] = _sbigudrv.GetCCDInfoResults0_readoutModes_set
    __swig_getmethods__["readoutModes"] = _sbigudrv.GetCCDInfoResults0_readoutModes_get
    if _newclass:readoutModes = property(_sbigudrv.GetCCDInfoResults0_readoutModes_get, _sbigudrv.GetCCDInfoResults0_readoutModes_set)
    __swig_setmethods__["readoutInfo"] = _sbigudrv.GetCCDInfoResults0_readoutInfo_set
    __swig_getmethods__["readoutInfo"] = _sbigudrv.GetCCDInfoResults0_readoutInfo_get
    if _newclass:readoutInfo = property(_sbigudrv.GetCCDInfoResults0_readoutInfo_get, _sbigudrv.GetCCDInfoResults0_readoutInfo_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetCCDInfoResults0(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetCCDInfoResults0
    __del__ = lambda self : None;
GetCCDInfoResults0_swigregister = _sbigudrv.GetCCDInfoResults0_swigregister
GetCCDInfoResults0_swigregister(GetCCDInfoResults0)

class GetCCDInfoResults2(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetCCDInfoResults2, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetCCDInfoResults2, name)
    __repr__ = _swig_repr
    __swig_setmethods__["badColumns"] = _sbigudrv.GetCCDInfoResults2_badColumns_set
    __swig_getmethods__["badColumns"] = _sbigudrv.GetCCDInfoResults2_badColumns_get
    if _newclass:badColumns = property(_sbigudrv.GetCCDInfoResults2_badColumns_get, _sbigudrv.GetCCDInfoResults2_badColumns_set)
    __swig_setmethods__["columns"] = _sbigudrv.GetCCDInfoResults2_columns_set
    __swig_getmethods__["columns"] = _sbigudrv.GetCCDInfoResults2_columns_get
    if _newclass:columns = property(_sbigudrv.GetCCDInfoResults2_columns_get, _sbigudrv.GetCCDInfoResults2_columns_set)
    __swig_setmethods__["imagingABG"] = _sbigudrv.GetCCDInfoResults2_imagingABG_set
    __swig_getmethods__["imagingABG"] = _sbigudrv.GetCCDInfoResults2_imagingABG_get
    if _newclass:imagingABG = property(_sbigudrv.GetCCDInfoResults2_imagingABG_get, _sbigudrv.GetCCDInfoResults2_imagingABG_set)
    __swig_setmethods__["serialNumber"] = _sbigudrv.GetCCDInfoResults2_serialNumber_set
    __swig_getmethods__["serialNumber"] = _sbigudrv.GetCCDInfoResults2_serialNumber_get
    if _newclass:serialNumber = property(_sbigudrv.GetCCDInfoResults2_serialNumber_get, _sbigudrv.GetCCDInfoResults2_serialNumber_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetCCDInfoResults2(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetCCDInfoResults2
    __del__ = lambda self : None;
GetCCDInfoResults2_swigregister = _sbigudrv.GetCCDInfoResults2_swigregister
GetCCDInfoResults2_swigregister(GetCCDInfoResults2)

class GetCCDInfoResults3(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetCCDInfoResults3, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetCCDInfoResults3, name)
    __repr__ = _swig_repr
    __swig_setmethods__["adSize"] = _sbigudrv.GetCCDInfoResults3_adSize_set
    __swig_getmethods__["adSize"] = _sbigudrv.GetCCDInfoResults3_adSize_get
    if _newclass:adSize = property(_sbigudrv.GetCCDInfoResults3_adSize_get, _sbigudrv.GetCCDInfoResults3_adSize_set)
    __swig_setmethods__["filterType"] = _sbigudrv.GetCCDInfoResults3_filterType_set
    __swig_getmethods__["filterType"] = _sbigudrv.GetCCDInfoResults3_filterType_get
    if _newclass:filterType = property(_sbigudrv.GetCCDInfoResults3_filterType_get, _sbigudrv.GetCCDInfoResults3_filterType_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetCCDInfoResults3(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetCCDInfoResults3
    __del__ = lambda self : None;
GetCCDInfoResults3_swigregister = _sbigudrv.GetCCDInfoResults3_swigregister
GetCCDInfoResults3_swigregister(GetCCDInfoResults3)

class GetCCDInfoResults4(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetCCDInfoResults4, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetCCDInfoResults4, name)
    __repr__ = _swig_repr
    __swig_setmethods__["capabilitiesBits"] = _sbigudrv.GetCCDInfoResults4_capabilitiesBits_set
    __swig_getmethods__["capabilitiesBits"] = _sbigudrv.GetCCDInfoResults4_capabilitiesBits_get
    if _newclass:capabilitiesBits = property(_sbigudrv.GetCCDInfoResults4_capabilitiesBits_get, _sbigudrv.GetCCDInfoResults4_capabilitiesBits_set)
    __swig_setmethods__["dumpExtra"] = _sbigudrv.GetCCDInfoResults4_dumpExtra_set
    __swig_getmethods__["dumpExtra"] = _sbigudrv.GetCCDInfoResults4_dumpExtra_get
    if _newclass:dumpExtra = property(_sbigudrv.GetCCDInfoResults4_dumpExtra_get, _sbigudrv.GetCCDInfoResults4_dumpExtra_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetCCDInfoResults4(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetCCDInfoResults4
    __del__ = lambda self : None;
GetCCDInfoResults4_swigregister = _sbigudrv.GetCCDInfoResults4_swigregister
GetCCDInfoResults4_swigregister(GetCCDInfoResults4)

class QueryCommandStatusParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, QueryCommandStatusParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, QueryCommandStatusParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["command"] = _sbigudrv.QueryCommandStatusParams_command_set
    __swig_getmethods__["command"] = _sbigudrv.QueryCommandStatusParams_command_get
    if _newclass:command = property(_sbigudrv.QueryCommandStatusParams_command_get, _sbigudrv.QueryCommandStatusParams_command_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_QueryCommandStatusParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_QueryCommandStatusParams
    __del__ = lambda self : None;
QueryCommandStatusParams_swigregister = _sbigudrv.QueryCommandStatusParams_swigregister
QueryCommandStatusParams_swigregister(QueryCommandStatusParams)

class QueryCommandStatusResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, QueryCommandStatusResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, QueryCommandStatusResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["status"] = _sbigudrv.QueryCommandStatusResults_status_set
    __swig_getmethods__["status"] = _sbigudrv.QueryCommandStatusResults_status_get
    if _newclass:status = property(_sbigudrv.QueryCommandStatusResults_status_get, _sbigudrv.QueryCommandStatusResults_status_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_QueryCommandStatusResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_QueryCommandStatusResults
    __del__ = lambda self : None;
QueryCommandStatusResults_swigregister = _sbigudrv.QueryCommandStatusResults_swigregister
QueryCommandStatusResults_swigregister(QueryCommandStatusResults)

class MiscellaneousControlParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, MiscellaneousControlParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, MiscellaneousControlParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["fanEnable"] = _sbigudrv.MiscellaneousControlParams_fanEnable_set
    __swig_getmethods__["fanEnable"] = _sbigudrv.MiscellaneousControlParams_fanEnable_get
    if _newclass:fanEnable = property(_sbigudrv.MiscellaneousControlParams_fanEnable_get, _sbigudrv.MiscellaneousControlParams_fanEnable_set)
    __swig_setmethods__["shutterCommand"] = _sbigudrv.MiscellaneousControlParams_shutterCommand_set
    __swig_getmethods__["shutterCommand"] = _sbigudrv.MiscellaneousControlParams_shutterCommand_get
    if _newclass:shutterCommand = property(_sbigudrv.MiscellaneousControlParams_shutterCommand_get, _sbigudrv.MiscellaneousControlParams_shutterCommand_set)
    __swig_setmethods__["ledState"] = _sbigudrv.MiscellaneousControlParams_ledState_set
    __swig_getmethods__["ledState"] = _sbigudrv.MiscellaneousControlParams_ledState_get
    if _newclass:ledState = property(_sbigudrv.MiscellaneousControlParams_ledState_get, _sbigudrv.MiscellaneousControlParams_ledState_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_MiscellaneousControlParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_MiscellaneousControlParams
    __del__ = lambda self : None;
MiscellaneousControlParams_swigregister = _sbigudrv.MiscellaneousControlParams_swigregister
MiscellaneousControlParams_swigregister(MiscellaneousControlParams)

class ReadOffsetParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ReadOffsetParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ReadOffsetParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.ReadOffsetParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.ReadOffsetParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.ReadOffsetParams_ccd_get, _sbigudrv.ReadOffsetParams_ccd_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_ReadOffsetParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_ReadOffsetParams
    __del__ = lambda self : None;
ReadOffsetParams_swigregister = _sbigudrv.ReadOffsetParams_swigregister
ReadOffsetParams_swigregister(ReadOffsetParams)

class ReadOffsetResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ReadOffsetResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ReadOffsetResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["offset"] = _sbigudrv.ReadOffsetResults_offset_set
    __swig_getmethods__["offset"] = _sbigudrv.ReadOffsetResults_offset_get
    if _newclass:offset = property(_sbigudrv.ReadOffsetResults_offset_get, _sbigudrv.ReadOffsetResults_offset_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_ReadOffsetResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_ReadOffsetResults
    __del__ = lambda self : None;
ReadOffsetResults_swigregister = _sbigudrv.ReadOffsetResults_swigregister
ReadOffsetResults_swigregister(ReadOffsetResults)

class AOTipTiltParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, AOTipTiltParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, AOTipTiltParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["xDeflection"] = _sbigudrv.AOTipTiltParams_xDeflection_set
    __swig_getmethods__["xDeflection"] = _sbigudrv.AOTipTiltParams_xDeflection_get
    if _newclass:xDeflection = property(_sbigudrv.AOTipTiltParams_xDeflection_get, _sbigudrv.AOTipTiltParams_xDeflection_set)
    __swig_setmethods__["yDeflection"] = _sbigudrv.AOTipTiltParams_yDeflection_set
    __swig_getmethods__["yDeflection"] = _sbigudrv.AOTipTiltParams_yDeflection_get
    if _newclass:yDeflection = property(_sbigudrv.AOTipTiltParams_yDeflection_get, _sbigudrv.AOTipTiltParams_yDeflection_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_AOTipTiltParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_AOTipTiltParams
    __del__ = lambda self : None;
AOTipTiltParams_swigregister = _sbigudrv.AOTipTiltParams_swigregister
AOTipTiltParams_swigregister(AOTipTiltParams)

class AOSetFocusParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, AOSetFocusParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, AOSetFocusParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["focusCommand"] = _sbigudrv.AOSetFocusParams_focusCommand_set
    __swig_getmethods__["focusCommand"] = _sbigudrv.AOSetFocusParams_focusCommand_get
    if _newclass:focusCommand = property(_sbigudrv.AOSetFocusParams_focusCommand_get, _sbigudrv.AOSetFocusParams_focusCommand_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_AOSetFocusParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_AOSetFocusParams
    __del__ = lambda self : None;
AOSetFocusParams_swigregister = _sbigudrv.AOSetFocusParams_swigregister
AOSetFocusParams_swigregister(AOSetFocusParams)

class AODelayParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, AODelayParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, AODelayParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["delay"] = _sbigudrv.AODelayParams_delay_set
    __swig_getmethods__["delay"] = _sbigudrv.AODelayParams_delay_get
    if _newclass:delay = property(_sbigudrv.AODelayParams_delay_get, _sbigudrv.AODelayParams_delay_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_AODelayParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_AODelayParams
    __del__ = lambda self : None;
AODelayParams_swigregister = _sbigudrv.AODelayParams_swigregister
AODelayParams_swigregister(AODelayParams)

class GetTurboStatusResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetTurboStatusResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetTurboStatusResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["turboDetected"] = _sbigudrv.GetTurboStatusResults_turboDetected_set
    __swig_getmethods__["turboDetected"] = _sbigudrv.GetTurboStatusResults_turboDetected_get
    if _newclass:turboDetected = property(_sbigudrv.GetTurboStatusResults_turboDetected_get, _sbigudrv.GetTurboStatusResults_turboDetected_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetTurboStatusResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetTurboStatusResults
    __del__ = lambda self : None;
GetTurboStatusResults_swigregister = _sbigudrv.GetTurboStatusResults_swigregister
GetTurboStatusResults_swigregister(GetTurboStatusResults)

class OpenDeviceParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, OpenDeviceParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, OpenDeviceParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["deviceType"] = _sbigudrv.OpenDeviceParams_deviceType_set
    __swig_getmethods__["deviceType"] = _sbigudrv.OpenDeviceParams_deviceType_get
    if _newclass:deviceType = property(_sbigudrv.OpenDeviceParams_deviceType_get, _sbigudrv.OpenDeviceParams_deviceType_set)
    __swig_setmethods__["lptBaseAddress"] = _sbigudrv.OpenDeviceParams_lptBaseAddress_set
    __swig_getmethods__["lptBaseAddress"] = _sbigudrv.OpenDeviceParams_lptBaseAddress_get
    if _newclass:lptBaseAddress = property(_sbigudrv.OpenDeviceParams_lptBaseAddress_get, _sbigudrv.OpenDeviceParams_lptBaseAddress_set)
    __swig_setmethods__["ipAddress"] = _sbigudrv.OpenDeviceParams_ipAddress_set
    __swig_getmethods__["ipAddress"] = _sbigudrv.OpenDeviceParams_ipAddress_get
    if _newclass:ipAddress = property(_sbigudrv.OpenDeviceParams_ipAddress_get, _sbigudrv.OpenDeviceParams_ipAddress_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_OpenDeviceParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_OpenDeviceParams
    __del__ = lambda self : None;
OpenDeviceParams_swigregister = _sbigudrv.OpenDeviceParams_swigregister
OpenDeviceParams_swigregister(OpenDeviceParams)

class SetIRQLParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SetIRQLParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SetIRQLParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["level"] = _sbigudrv.SetIRQLParams_level_set
    __swig_getmethods__["level"] = _sbigudrv.SetIRQLParams_level_get
    if _newclass:level = property(_sbigudrv.SetIRQLParams_level_get, _sbigudrv.SetIRQLParams_level_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SetIRQLParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SetIRQLParams
    __del__ = lambda self : None;
SetIRQLParams_swigregister = _sbigudrv.SetIRQLParams_swigregister
SetIRQLParams_swigregister(SetIRQLParams)

class GetIRQLResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetIRQLResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetIRQLResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["level"] = _sbigudrv.GetIRQLResults_level_set
    __swig_getmethods__["level"] = _sbigudrv.GetIRQLResults_level_get
    if _newclass:level = property(_sbigudrv.GetIRQLResults_level_get, _sbigudrv.GetIRQLResults_level_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetIRQLResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetIRQLResults
    __del__ = lambda self : None;
GetIRQLResults_swigregister = _sbigudrv.GetIRQLResults_swigregister
GetIRQLResults_swigregister(GetIRQLResults)

class GetLinkStatusResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetLinkStatusResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetLinkStatusResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["linkEstablished"] = _sbigudrv.GetLinkStatusResults_linkEstablished_set
    __swig_getmethods__["linkEstablished"] = _sbigudrv.GetLinkStatusResults_linkEstablished_get
    if _newclass:linkEstablished = property(_sbigudrv.GetLinkStatusResults_linkEstablished_get, _sbigudrv.GetLinkStatusResults_linkEstablished_set)
    __swig_setmethods__["baseAddress"] = _sbigudrv.GetLinkStatusResults_baseAddress_set
    __swig_getmethods__["baseAddress"] = _sbigudrv.GetLinkStatusResults_baseAddress_get
    if _newclass:baseAddress = property(_sbigudrv.GetLinkStatusResults_baseAddress_get, _sbigudrv.GetLinkStatusResults_baseAddress_set)
    __swig_setmethods__["cameraType"] = _sbigudrv.GetLinkStatusResults_cameraType_set
    __swig_getmethods__["cameraType"] = _sbigudrv.GetLinkStatusResults_cameraType_get
    if _newclass:cameraType = property(_sbigudrv.GetLinkStatusResults_cameraType_get, _sbigudrv.GetLinkStatusResults_cameraType_set)
    __swig_setmethods__["comTotal"] = _sbigudrv.GetLinkStatusResults_comTotal_set
    __swig_getmethods__["comTotal"] = _sbigudrv.GetLinkStatusResults_comTotal_get
    if _newclass:comTotal = property(_sbigudrv.GetLinkStatusResults_comTotal_get, _sbigudrv.GetLinkStatusResults_comTotal_set)
    __swig_setmethods__["comFailed"] = _sbigudrv.GetLinkStatusResults_comFailed_set
    __swig_getmethods__["comFailed"] = _sbigudrv.GetLinkStatusResults_comFailed_get
    if _newclass:comFailed = property(_sbigudrv.GetLinkStatusResults_comFailed_get, _sbigudrv.GetLinkStatusResults_comFailed_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetLinkStatusResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetLinkStatusResults
    __del__ = lambda self : None;
GetLinkStatusResults_swigregister = _sbigudrv.GetLinkStatusResults_swigregister
GetLinkStatusResults_swigregister(GetLinkStatusResults)

class GetUSTimerResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetUSTimerResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetUSTimerResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["count"] = _sbigudrv.GetUSTimerResults_count_set
    __swig_getmethods__["count"] = _sbigudrv.GetUSTimerResults_count_get
    if _newclass:count = property(_sbigudrv.GetUSTimerResults_count_get, _sbigudrv.GetUSTimerResults_count_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetUSTimerResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetUSTimerResults
    __del__ = lambda self : None;
GetUSTimerResults_swigregister = _sbigudrv.GetUSTimerResults_swigregister
GetUSTimerResults_swigregister(GetUSTimerResults)

class SendBlockParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SendBlockParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SendBlockParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["port"] = _sbigudrv.SendBlockParams_port_set
    __swig_getmethods__["port"] = _sbigudrv.SendBlockParams_port_get
    if _newclass:port = property(_sbigudrv.SendBlockParams_port_get, _sbigudrv.SendBlockParams_port_set)
    __swig_setmethods__["length"] = _sbigudrv.SendBlockParams_length_set
    __swig_getmethods__["length"] = _sbigudrv.SendBlockParams_length_get
    if _newclass:length = property(_sbigudrv.SendBlockParams_length_get, _sbigudrv.SendBlockParams_length_set)
    __swig_setmethods__["source"] = _sbigudrv.SendBlockParams_source_set
    __swig_getmethods__["source"] = _sbigudrv.SendBlockParams_source_get
    if _newclass:source = property(_sbigudrv.SendBlockParams_source_get, _sbigudrv.SendBlockParams_source_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SendBlockParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SendBlockParams
    __del__ = lambda self : None;
SendBlockParams_swigregister = _sbigudrv.SendBlockParams_swigregister
SendBlockParams_swigregister(SendBlockParams)

class SendByteParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SendByteParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SendByteParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["port"] = _sbigudrv.SendByteParams_port_set
    __swig_getmethods__["port"] = _sbigudrv.SendByteParams_port_get
    if _newclass:port = property(_sbigudrv.SendByteParams_port_get, _sbigudrv.SendByteParams_port_set)
    __swig_setmethods__["data"] = _sbigudrv.SendByteParams_data_set
    __swig_getmethods__["data"] = _sbigudrv.SendByteParams_data_get
    if _newclass:data = property(_sbigudrv.SendByteParams_data_get, _sbigudrv.SendByteParams_data_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SendByteParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SendByteParams
    __del__ = lambda self : None;
SendByteParams_swigregister = _sbigudrv.SendByteParams_swigregister
SendByteParams_swigregister(SendByteParams)

class ClockADParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, ClockADParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, ClockADParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["ccd"] = _sbigudrv.ClockADParams_ccd_set
    __swig_getmethods__["ccd"] = _sbigudrv.ClockADParams_ccd_get
    if _newclass:ccd = property(_sbigudrv.ClockADParams_ccd_get, _sbigudrv.ClockADParams_ccd_set)
    __swig_setmethods__["readoutMode"] = _sbigudrv.ClockADParams_readoutMode_set
    __swig_getmethods__["readoutMode"] = _sbigudrv.ClockADParams_readoutMode_get
    if _newclass:readoutMode = property(_sbigudrv.ClockADParams_readoutMode_get, _sbigudrv.ClockADParams_readoutMode_set)
    __swig_setmethods__["pixelStart"] = _sbigudrv.ClockADParams_pixelStart_set
    __swig_getmethods__["pixelStart"] = _sbigudrv.ClockADParams_pixelStart_get
    if _newclass:pixelStart = property(_sbigudrv.ClockADParams_pixelStart_get, _sbigudrv.ClockADParams_pixelStart_set)
    __swig_setmethods__["pixelLength"] = _sbigudrv.ClockADParams_pixelLength_set
    __swig_getmethods__["pixelLength"] = _sbigudrv.ClockADParams_pixelLength_get
    if _newclass:pixelLength = property(_sbigudrv.ClockADParams_pixelLength_get, _sbigudrv.ClockADParams_pixelLength_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_ClockADParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_ClockADParams
    __del__ = lambda self : None;
ClockADParams_swigregister = _sbigudrv.ClockADParams_swigregister
ClockADParams_swigregister(ClockADParams)

class SystemTestParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SystemTestParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SystemTestParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["testClocks"] = _sbigudrv.SystemTestParams_testClocks_set
    __swig_getmethods__["testClocks"] = _sbigudrv.SystemTestParams_testClocks_get
    if _newclass:testClocks = property(_sbigudrv.SystemTestParams_testClocks_get, _sbigudrv.SystemTestParams_testClocks_set)
    __swig_setmethods__["testMotor"] = _sbigudrv.SystemTestParams_testMotor_set
    __swig_getmethods__["testMotor"] = _sbigudrv.SystemTestParams_testMotor_get
    if _newclass:testMotor = property(_sbigudrv.SystemTestParams_testMotor_get, _sbigudrv.SystemTestParams_testMotor_set)
    __swig_setmethods__["test5800"] = _sbigudrv.SystemTestParams_test5800_set
    __swig_getmethods__["test5800"] = _sbigudrv.SystemTestParams_test5800_get
    if _newclass:test5800 = property(_sbigudrv.SystemTestParams_test5800_get, _sbigudrv.SystemTestParams_test5800_set)
    __swig_setmethods__["stlAlign"] = _sbigudrv.SystemTestParams_stlAlign_set
    __swig_getmethods__["stlAlign"] = _sbigudrv.SystemTestParams_stlAlign_get
    if _newclass:stlAlign = property(_sbigudrv.SystemTestParams_stlAlign_get, _sbigudrv.SystemTestParams_stlAlign_set)
    __swig_setmethods__["motorAlwaysOn"] = _sbigudrv.SystemTestParams_motorAlwaysOn_set
    __swig_getmethods__["motorAlwaysOn"] = _sbigudrv.SystemTestParams_motorAlwaysOn_get
    if _newclass:motorAlwaysOn = property(_sbigudrv.SystemTestParams_motorAlwaysOn_get, _sbigudrv.SystemTestParams_motorAlwaysOn_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SystemTestParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SystemTestParams
    __del__ = lambda self : None;
SystemTestParams_swigregister = _sbigudrv.SystemTestParams_swigregister
SystemTestParams_swigregister(SystemTestParams)

class SendSTVBlockParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SendSTVBlockParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SendSTVBlockParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["outLength"] = _sbigudrv.SendSTVBlockParams_outLength_set
    __swig_getmethods__["outLength"] = _sbigudrv.SendSTVBlockParams_outLength_get
    if _newclass:outLength = property(_sbigudrv.SendSTVBlockParams_outLength_get, _sbigudrv.SendSTVBlockParams_outLength_set)
    __swig_setmethods__["outPtr"] = _sbigudrv.SendSTVBlockParams_outPtr_set
    __swig_getmethods__["outPtr"] = _sbigudrv.SendSTVBlockParams_outPtr_get
    if _newclass:outPtr = property(_sbigudrv.SendSTVBlockParams_outPtr_get, _sbigudrv.SendSTVBlockParams_outPtr_set)
    __swig_setmethods__["inLength"] = _sbigudrv.SendSTVBlockParams_inLength_set
    __swig_getmethods__["inLength"] = _sbigudrv.SendSTVBlockParams_inLength_get
    if _newclass:inLength = property(_sbigudrv.SendSTVBlockParams_inLength_get, _sbigudrv.SendSTVBlockParams_inLength_set)
    __swig_setmethods__["inPtr"] = _sbigudrv.SendSTVBlockParams_inPtr_set
    __swig_getmethods__["inPtr"] = _sbigudrv.SendSTVBlockParams_inPtr_get
    if _newclass:inPtr = property(_sbigudrv.SendSTVBlockParams_inPtr_get, _sbigudrv.SendSTVBlockParams_inPtr_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SendSTVBlockParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SendSTVBlockParams
    __del__ = lambda self : None;
SendSTVBlockParams_swigregister = _sbigudrv.SendSTVBlockParams_swigregister
SendSTVBlockParams_swigregister(SendSTVBlockParams)

class GetErrorStringParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetErrorStringParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetErrorStringParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["errorNo"] = _sbigudrv.GetErrorStringParams_errorNo_set
    __swig_getmethods__["errorNo"] = _sbigudrv.GetErrorStringParams_errorNo_get
    if _newclass:errorNo = property(_sbigudrv.GetErrorStringParams_errorNo_get, _sbigudrv.GetErrorStringParams_errorNo_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetErrorStringParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetErrorStringParams
    __del__ = lambda self : None;
GetErrorStringParams_swigregister = _sbigudrv.GetErrorStringParams_swigregister
GetErrorStringParams_swigregister(GetErrorStringParams)

class GetErrorStringResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetErrorStringResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetErrorStringResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["errorString"] = _sbigudrv.GetErrorStringResults_errorString_set
    __swig_getmethods__["errorString"] = _sbigudrv.GetErrorStringResults_errorString_get
    if _newclass:errorString = property(_sbigudrv.GetErrorStringResults_errorString_get, _sbigudrv.GetErrorStringResults_errorString_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetErrorStringResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetErrorStringResults
    __del__ = lambda self : None;
GetErrorStringResults_swigregister = _sbigudrv.GetErrorStringResults_swigregister
GetErrorStringResults_swigregister(GetErrorStringResults)

class SetDriverHandleParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SetDriverHandleParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SetDriverHandleParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["handle"] = _sbigudrv.SetDriverHandleParams_handle_set
    __swig_getmethods__["handle"] = _sbigudrv.SetDriverHandleParams_handle_get
    if _newclass:handle = property(_sbigudrv.SetDriverHandleParams_handle_get, _sbigudrv.SetDriverHandleParams_handle_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SetDriverHandleParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SetDriverHandleParams
    __del__ = lambda self : None;
SetDriverHandleParams_swigregister = _sbigudrv.SetDriverHandleParams_swigregister
SetDriverHandleParams_swigregister(SetDriverHandleParams)

class GetDriverHandleResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetDriverHandleResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetDriverHandleResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["handle"] = _sbigudrv.GetDriverHandleResults_handle_set
    __swig_getmethods__["handle"] = _sbigudrv.GetDriverHandleResults_handle_get
    if _newclass:handle = property(_sbigudrv.GetDriverHandleResults_handle_get, _sbigudrv.GetDriverHandleResults_handle_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetDriverHandleResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetDriverHandleResults
    __del__ = lambda self : None;
GetDriverHandleResults_swigregister = _sbigudrv.GetDriverHandleResults_swigregister
GetDriverHandleResults_swigregister(GetDriverHandleResults)

class SetDriverControlParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SetDriverControlParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SetDriverControlParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["controlParameter"] = _sbigudrv.SetDriverControlParams_controlParameter_set
    __swig_getmethods__["controlParameter"] = _sbigudrv.SetDriverControlParams_controlParameter_get
    if _newclass:controlParameter = property(_sbigudrv.SetDriverControlParams_controlParameter_get, _sbigudrv.SetDriverControlParams_controlParameter_set)
    __swig_setmethods__["controlValue"] = _sbigudrv.SetDriverControlParams_controlValue_set
    __swig_getmethods__["controlValue"] = _sbigudrv.SetDriverControlParams_controlValue_get
    if _newclass:controlValue = property(_sbigudrv.SetDriverControlParams_controlValue_get, _sbigudrv.SetDriverControlParams_controlValue_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_SetDriverControlParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_SetDriverControlParams
    __del__ = lambda self : None;
SetDriverControlParams_swigregister = _sbigudrv.SetDriverControlParams_swigregister
SetDriverControlParams_swigregister(SetDriverControlParams)

class GetDriverControlParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetDriverControlParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetDriverControlParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["controlParameter"] = _sbigudrv.GetDriverControlParams_controlParameter_set
    __swig_getmethods__["controlParameter"] = _sbigudrv.GetDriverControlParams_controlParameter_get
    if _newclass:controlParameter = property(_sbigudrv.GetDriverControlParams_controlParameter_get, _sbigudrv.GetDriverControlParams_controlParameter_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetDriverControlParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetDriverControlParams
    __del__ = lambda self : None;
GetDriverControlParams_swigregister = _sbigudrv.GetDriverControlParams_swigregister
GetDriverControlParams_swigregister(GetDriverControlParams)

class GetDriverControlResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetDriverControlResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetDriverControlResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["controlValue"] = _sbigudrv.GetDriverControlResults_controlValue_set
    __swig_getmethods__["controlValue"] = _sbigudrv.GetDriverControlResults_controlValue_get
    if _newclass:controlValue = property(_sbigudrv.GetDriverControlResults_controlValue_get, _sbigudrv.GetDriverControlResults_controlValue_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetDriverControlResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetDriverControlResults
    __del__ = lambda self : None;
GetDriverControlResults_swigregister = _sbigudrv.GetDriverControlResults_swigregister
GetDriverControlResults_swigregister(GetDriverControlResults)

class USBADControlParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, USBADControlParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, USBADControlParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["command"] = _sbigudrv.USBADControlParams_command_set
    __swig_getmethods__["command"] = _sbigudrv.USBADControlParams_command_get
    if _newclass:command = property(_sbigudrv.USBADControlParams_command_get, _sbigudrv.USBADControlParams_command_set)
    __swig_setmethods__["data"] = _sbigudrv.USBADControlParams_data_set
    __swig_getmethods__["data"] = _sbigudrv.USBADControlParams_data_get
    if _newclass:data = property(_sbigudrv.USBADControlParams_data_get, _sbigudrv.USBADControlParams_data_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_USBADControlParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_USBADControlParams
    __del__ = lambda self : None;
USBADControlParams_swigregister = _sbigudrv.USBADControlParams_swigregister
USBADControlParams_swigregister(USBADControlParams)

class QUERY_USB_INFO(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, QUERY_USB_INFO, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, QUERY_USB_INFO, name)
    __repr__ = _swig_repr
    __swig_setmethods__["cameraFound"] = _sbigudrv.QUERY_USB_INFO_cameraFound_set
    __swig_getmethods__["cameraFound"] = _sbigudrv.QUERY_USB_INFO_cameraFound_get
    if _newclass:cameraFound = property(_sbigudrv.QUERY_USB_INFO_cameraFound_get, _sbigudrv.QUERY_USB_INFO_cameraFound_set)
    __swig_setmethods__["cameraType"] = _sbigudrv.QUERY_USB_INFO_cameraType_set
    __swig_getmethods__["cameraType"] = _sbigudrv.QUERY_USB_INFO_cameraType_get
    if _newclass:cameraType = property(_sbigudrv.QUERY_USB_INFO_cameraType_get, _sbigudrv.QUERY_USB_INFO_cameraType_set)
    __swig_setmethods__["name"] = _sbigudrv.QUERY_USB_INFO_name_set
    __swig_getmethods__["name"] = _sbigudrv.QUERY_USB_INFO_name_get
    if _newclass:name = property(_sbigudrv.QUERY_USB_INFO_name_get, _sbigudrv.QUERY_USB_INFO_name_set)
    __swig_setmethods__["serialNumber"] = _sbigudrv.QUERY_USB_INFO_serialNumber_set
    __swig_getmethods__["serialNumber"] = _sbigudrv.QUERY_USB_INFO_serialNumber_get
    if _newclass:serialNumber = property(_sbigudrv.QUERY_USB_INFO_serialNumber_get, _sbigudrv.QUERY_USB_INFO_serialNumber_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_QUERY_USB_INFO(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_QUERY_USB_INFO
    __del__ = lambda self : None;
QUERY_USB_INFO_swigregister = _sbigudrv.QUERY_USB_INFO_swigregister
QUERY_USB_INFO_swigregister(QUERY_USB_INFO)

class QueryUSBResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, QueryUSBResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, QueryUSBResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["camerasFound"] = _sbigudrv.QueryUSBResults_camerasFound_set
    __swig_getmethods__["camerasFound"] = _sbigudrv.QueryUSBResults_camerasFound_get
    if _newclass:camerasFound = property(_sbigudrv.QueryUSBResults_camerasFound_get, _sbigudrv.QueryUSBResults_camerasFound_set)
    __swig_setmethods__["usbInfo"] = _sbigudrv.QueryUSBResults_usbInfo_set
    __swig_getmethods__["usbInfo"] = _sbigudrv.QueryUSBResults_usbInfo_get
    if _newclass:usbInfo = property(_sbigudrv.QueryUSBResults_usbInfo_get, _sbigudrv.QueryUSBResults_usbInfo_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_QueryUSBResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_QueryUSBResults
    __del__ = lambda self : None;
QueryUSBResults_swigregister = _sbigudrv.QueryUSBResults_swigregister
QueryUSBResults_swigregister(QueryUSBResults)

class GetPentiumCycleCountParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetPentiumCycleCountParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetPentiumCycleCountParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["rightShift"] = _sbigudrv.GetPentiumCycleCountParams_rightShift_set
    __swig_getmethods__["rightShift"] = _sbigudrv.GetPentiumCycleCountParams_rightShift_get
    if _newclass:rightShift = property(_sbigudrv.GetPentiumCycleCountParams_rightShift_get, _sbigudrv.GetPentiumCycleCountParams_rightShift_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetPentiumCycleCountParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetPentiumCycleCountParams
    __del__ = lambda self : None;
GetPentiumCycleCountParams_swigregister = _sbigudrv.GetPentiumCycleCountParams_swigregister
GetPentiumCycleCountParams_swigregister(GetPentiumCycleCountParams)

class GetPentiumCycleCountResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, GetPentiumCycleCountResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, GetPentiumCycleCountResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["countLow"] = _sbigudrv.GetPentiumCycleCountResults_countLow_set
    __swig_getmethods__["countLow"] = _sbigudrv.GetPentiumCycleCountResults_countLow_get
    if _newclass:countLow = property(_sbigudrv.GetPentiumCycleCountResults_countLow_get, _sbigudrv.GetPentiumCycleCountResults_countLow_set)
    __swig_setmethods__["countHigh"] = _sbigudrv.GetPentiumCycleCountResults_countHigh_set
    __swig_getmethods__["countHigh"] = _sbigudrv.GetPentiumCycleCountResults_countHigh_get
    if _newclass:countHigh = property(_sbigudrv.GetPentiumCycleCountResults_countHigh_get, _sbigudrv.GetPentiumCycleCountResults_countHigh_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_GetPentiumCycleCountResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_GetPentiumCycleCountResults
    __del__ = lambda self : None;
GetPentiumCycleCountResults_swigregister = _sbigudrv.GetPentiumCycleCountResults_swigregister
GetPentiumCycleCountResults_swigregister(GetPentiumCycleCountResults)

class RWUSBI2CParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RWUSBI2CParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RWUSBI2CParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["address"] = _sbigudrv.RWUSBI2CParams_address_set
    __swig_getmethods__["address"] = _sbigudrv.RWUSBI2CParams_address_get
    if _newclass:address = property(_sbigudrv.RWUSBI2CParams_address_get, _sbigudrv.RWUSBI2CParams_address_set)
    __swig_setmethods__["data"] = _sbigudrv.RWUSBI2CParams_data_set
    __swig_getmethods__["data"] = _sbigudrv.RWUSBI2CParams_data_get
    if _newclass:data = property(_sbigudrv.RWUSBI2CParams_data_get, _sbigudrv.RWUSBI2CParams_data_set)
    __swig_setmethods__["write"] = _sbigudrv.RWUSBI2CParams_write_set
    __swig_getmethods__["write"] = _sbigudrv.RWUSBI2CParams_write_get
    if _newclass:write = property(_sbigudrv.RWUSBI2CParams_write_get, _sbigudrv.RWUSBI2CParams_write_set)
    __swig_setmethods__["deviceAddress"] = _sbigudrv.RWUSBI2CParams_deviceAddress_set
    __swig_getmethods__["deviceAddress"] = _sbigudrv.RWUSBI2CParams_deviceAddress_get
    if _newclass:deviceAddress = property(_sbigudrv.RWUSBI2CParams_deviceAddress_get, _sbigudrv.RWUSBI2CParams_deviceAddress_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_RWUSBI2CParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_RWUSBI2CParams
    __del__ = lambda self : None;
RWUSBI2CParams_swigregister = _sbigudrv.RWUSBI2CParams_swigregister
RWUSBI2CParams_swigregister(RWUSBI2CParams)

class RWUSBI2CResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, RWUSBI2CResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, RWUSBI2CResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["data"] = _sbigudrv.RWUSBI2CResults_data_set
    __swig_getmethods__["data"] = _sbigudrv.RWUSBI2CResults_data_get
    if _newclass:data = property(_sbigudrv.RWUSBI2CResults_data_get, _sbigudrv.RWUSBI2CResults_data_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_RWUSBI2CResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_RWUSBI2CResults
    __del__ = lambda self : None;
RWUSBI2CResults_swigregister = _sbigudrv.RWUSBI2CResults_swigregister
RWUSBI2CResults_swigregister(RWUSBI2CResults)

class CFWParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CFWParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CFWParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["cfwModel"] = _sbigudrv.CFWParams_cfwModel_set
    __swig_getmethods__["cfwModel"] = _sbigudrv.CFWParams_cfwModel_get
    if _newclass:cfwModel = property(_sbigudrv.CFWParams_cfwModel_get, _sbigudrv.CFWParams_cfwModel_set)
    __swig_setmethods__["cfwCommand"] = _sbigudrv.CFWParams_cfwCommand_set
    __swig_getmethods__["cfwCommand"] = _sbigudrv.CFWParams_cfwCommand_get
    if _newclass:cfwCommand = property(_sbigudrv.CFWParams_cfwCommand_get, _sbigudrv.CFWParams_cfwCommand_set)
    __swig_setmethods__["cwfParam1"] = _sbigudrv.CFWParams_cwfParam1_set
    __swig_getmethods__["cwfParam1"] = _sbigudrv.CFWParams_cwfParam1_get
    if _newclass:cwfParam1 = property(_sbigudrv.CFWParams_cwfParam1_get, _sbigudrv.CFWParams_cwfParam1_set)
    __swig_setmethods__["cfwParam2"] = _sbigudrv.CFWParams_cfwParam2_set
    __swig_getmethods__["cfwParam2"] = _sbigudrv.CFWParams_cfwParam2_get
    if _newclass:cfwParam2 = property(_sbigudrv.CFWParams_cfwParam2_get, _sbigudrv.CFWParams_cfwParam2_set)
    __swig_setmethods__["outLength"] = _sbigudrv.CFWParams_outLength_set
    __swig_getmethods__["outLength"] = _sbigudrv.CFWParams_outLength_get
    if _newclass:outLength = property(_sbigudrv.CFWParams_outLength_get, _sbigudrv.CFWParams_outLength_set)
    __swig_setmethods__["outPtr"] = _sbigudrv.CFWParams_outPtr_set
    __swig_getmethods__["outPtr"] = _sbigudrv.CFWParams_outPtr_get
    if _newclass:outPtr = property(_sbigudrv.CFWParams_outPtr_get, _sbigudrv.CFWParams_outPtr_set)
    __swig_setmethods__["inLength"] = _sbigudrv.CFWParams_inLength_set
    __swig_getmethods__["inLength"] = _sbigudrv.CFWParams_inLength_get
    if _newclass:inLength = property(_sbigudrv.CFWParams_inLength_get, _sbigudrv.CFWParams_inLength_set)
    __swig_setmethods__["inPtr"] = _sbigudrv.CFWParams_inPtr_set
    __swig_getmethods__["inPtr"] = _sbigudrv.CFWParams_inPtr_get
    if _newclass:inPtr = property(_sbigudrv.CFWParams_inPtr_get, _sbigudrv.CFWParams_inPtr_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_CFWParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_CFWParams
    __del__ = lambda self : None;
CFWParams_swigregister = _sbigudrv.CFWParams_swigregister
CFWParams_swigregister(CFWParams)

class CFWResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CFWResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CFWResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["cfwModel"] = _sbigudrv.CFWResults_cfwModel_set
    __swig_getmethods__["cfwModel"] = _sbigudrv.CFWResults_cfwModel_get
    if _newclass:cfwModel = property(_sbigudrv.CFWResults_cfwModel_get, _sbigudrv.CFWResults_cfwModel_set)
    __swig_setmethods__["cfwPosition"] = _sbigudrv.CFWResults_cfwPosition_set
    __swig_getmethods__["cfwPosition"] = _sbigudrv.CFWResults_cfwPosition_get
    if _newclass:cfwPosition = property(_sbigudrv.CFWResults_cfwPosition_get, _sbigudrv.CFWResults_cfwPosition_set)
    __swig_setmethods__["cfwStatus"] = _sbigudrv.CFWResults_cfwStatus_set
    __swig_getmethods__["cfwStatus"] = _sbigudrv.CFWResults_cfwStatus_get
    if _newclass:cfwStatus = property(_sbigudrv.CFWResults_cfwStatus_get, _sbigudrv.CFWResults_cfwStatus_set)
    __swig_setmethods__["cfwError"] = _sbigudrv.CFWResults_cfwError_set
    __swig_getmethods__["cfwError"] = _sbigudrv.CFWResults_cfwError_get
    if _newclass:cfwError = property(_sbigudrv.CFWResults_cfwError_get, _sbigudrv.CFWResults_cfwError_set)
    __swig_setmethods__["cfwResult1"] = _sbigudrv.CFWResults_cfwResult1_set
    __swig_getmethods__["cfwResult1"] = _sbigudrv.CFWResults_cfwResult1_get
    if _newclass:cfwResult1 = property(_sbigudrv.CFWResults_cfwResult1_get, _sbigudrv.CFWResults_cfwResult1_set)
    __swig_setmethods__["cfwResult2"] = _sbigudrv.CFWResults_cfwResult2_set
    __swig_getmethods__["cfwResult2"] = _sbigudrv.CFWResults_cfwResult2_get
    if _newclass:cfwResult2 = property(_sbigudrv.CFWResults_cfwResult2_get, _sbigudrv.CFWResults_cfwResult2_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_CFWResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_CFWResults
    __del__ = lambda self : None;
CFWResults_swigregister = _sbigudrv.CFWResults_swigregister
CFWResults_swigregister(CFWResults)

class BitIOParams(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, BitIOParams, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, BitIOParams, name)
    __repr__ = _swig_repr
    __swig_setmethods__["bitOperation"] = _sbigudrv.BitIOParams_bitOperation_set
    __swig_getmethods__["bitOperation"] = _sbigudrv.BitIOParams_bitOperation_get
    if _newclass:bitOperation = property(_sbigudrv.BitIOParams_bitOperation_get, _sbigudrv.BitIOParams_bitOperation_set)
    __swig_setmethods__["bitName"] = _sbigudrv.BitIOParams_bitName_set
    __swig_getmethods__["bitName"] = _sbigudrv.BitIOParams_bitName_get
    if _newclass:bitName = property(_sbigudrv.BitIOParams_bitName_get, _sbigudrv.BitIOParams_bitName_set)
    __swig_setmethods__["setBit"] = _sbigudrv.BitIOParams_setBit_set
    __swig_getmethods__["setBit"] = _sbigudrv.BitIOParams_setBit_get
    if _newclass:setBit = property(_sbigudrv.BitIOParams_setBit_get, _sbigudrv.BitIOParams_setBit_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_BitIOParams(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_BitIOParams
    __del__ = lambda self : None;
BitIOParams_swigregister = _sbigudrv.BitIOParams_swigregister
BitIOParams_swigregister(BitIOParams)

class BitIOResults(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, BitIOResults, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, BitIOResults, name)
    __repr__ = _swig_repr
    __swig_setmethods__["bitIsSet"] = _sbigudrv.BitIOResults_bitIsSet_set
    __swig_getmethods__["bitIsSet"] = _sbigudrv.BitIOResults_bitIsSet_get
    if _newclass:bitIsSet = property(_sbigudrv.BitIOResults_bitIsSet_get, _sbigudrv.BitIOResults_bitIsSet_set)
    def __init__(self, *args): 
        this = _sbigudrv.new_BitIOResults(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _sbigudrv.delete_BitIOResults
    __del__ = lambda self : None;
BitIOResults_swigregister = _sbigudrv.BitIOResults_swigregister
BitIOResults_swigregister(BitIOResults)

SBIGUnivDrvCommand = _sbigudrv.SBIGUnivDrvCommand


