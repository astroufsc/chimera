#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import math

import numpy
import sbigudrv as udrv

import logging
from chimera.core.log import logging
from chimera.util.dumper import dumpObj

log = logging.getLogger(__name__)

from chimera.core.exceptions import ChimeraException


class SBIGException (ChimeraException):

    def __init__ (self, code, msg=""):
        ChimeraException.__init__(self, msg)
        self.code = code

    def __str__ (self):
        return "%s (%d)" % (self.message, self.code)


class ReadoutMode(object):

    def __init__(self, mode):
        self.mode =  mode.mode
        self.gain = float(hex(mode.gain).split('x')[1]) / 100.0
        self.width = mode.width
        self.height = mode.height
        self.pixelWidth = float(hex(mode.pixel_width).split('x')[1]) / 100.0
        self.pixelHeight = float(hex(mode.pixel_height).split('x')[1]) / 100.0

    def getSize(self):
        return (self.width, self.height)

    def getInternalSize(self):
        return (self.height, self.width)

    def getWindow(self):
        return [0, 0, self.width, self.height]

    def getPixelSize(self):
        return (self.pixelWidth, self.pixelHeight)

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


class TemperatureSetPoint(object):

    t0 = 25.0
    r0 = 3.0
    max_ad = 4096

    r_ratio = {"ccd": 2.57,
               "amb": 7.791}

    r_bridge = {"ccd": 10.0,
                "amb": 3.0}

    dt = {"ccd": 25.0,
          "amb": 45.0}

    @classmethod
    def toAD (cls, temp, sensor = "ccd"):

        if sensor not in ["ccd", "amb"]:
            sensor = "ccd"

        temp = float(temp)

        # limits from CSBIGCam
        if temp < -50.0:
            temp = -50.0
        elif temp > 35.0:
            temp = 35.0
        
        r = cls.r0 * math.exp ((math.log (cls.r_ratio[sensor]) * (cls.t0 - temp)) / cls.dt[sensor])

        SetPoint = (cls.max_ad / ((cls.r_bridge[sensor] / r) + 1.0)) + 0.5

        #print "from %f to %d" % (temp, int(SetPoint))

        return int(SetPoint)

    @classmethod
    def toDegrees (cls, SetPoint, sensor = "ccd"):

        if sensor not in ["ccd", "amb"]:
            sensor = "ccd"

        SetPoint = int (SetPoint)

        # limits from CSBIGCam
        if SetPoint < 1:
            SetPoint = 1
        elif SetPoint >= (cls.max_ad - 1):
            SetPoint = cls.max_ad - 1

        r = cls.r_bridge[sensor] / ((float(cls.max_ad) / SetPoint) - 1.0)

        temp = cls.t0 - (cls.dt[sensor] * (math.log (r/cls.r0) / math.log (cls.r_ratio[sensor])))

        #print "from %f to %f" % (SetPoint, temp)

        return temp
 

class SBIGDrv(object):

    lpt1 = udrv.DEV_LPT1
    lpt2 = udrv.DEV_LPT2
    lpt3 = udrv.DEV_LPT3
    usb  = udrv.DEV_USB
    usb1 = udrv.DEV_USB1
    usb2 = udrv.DEV_USB2
    usb3 = udrv.DEV_USB3
    usb4 = udrv.DEV_USB4
    
    imaging = udrv.CCD_IMAGING
    tracking = udrv.CCD_TRACKING

    openShutter  = udrv.SC_OPEN_SHUTTER
    closeShutter = udrv.SC_CLOSE_SHUTTER
    leaveShutter = udrv.SC_LEAVE_SHUTTER

    readoutModes = {imaging: {},
                    tracking: {}}

    filters = {1: udrv.CFWP_1,
               2: udrv.CFWP_2,
               3: udrv.CFWP_3,
               4: udrv.CFWP_4,
               5: udrv.CFWP_5}

    # private
    _imgIdle       = 0x0
    _imgInProgress = 0x2
    _imgComplete   = 0x3
    _trkIdle       = 0x0
    _trkInProgress = 0x8
    _trkComplete   = 0xc

    def __init__(self):
        #FIXME: check device permissions and module status
        pass

    def openDriver(self):

        try:
            return self._cmd(udrv.CC_OPEN_DRIVER, None, None)
        except SBIGException, e:
            if e.code == udrv.CE_DRIVER_NOT_CLOSED:
                # driver already open (are you trying to use the tracking ccd?)
                return True
            else:
                raise

    def closeDriver(self):
        return self._cmd(udrv.CC_CLOSE_DRIVER, None, None)

    def openDevice(self, device):

        odp = udrv.OpenDeviceParams()
        odp.deviceType = device

        try:
            return self._cmd(udrv.CC_OPEN_DEVICE, odp, None)
        except SBIGException, e:
            if e.code == udrv.CE_DEVICE_NOT_CLOSED:
                # device already open (are you trying to use the tracking ccd?)
                return True
            else:
                raise

    def closeDevice(self):
        return self._cmd(udrv.CC_CLOSE_DEVICE, None, None)

    def establishLink(self):
        elp = udrv.EstablishLinkParams()
        elr = udrv.EstablishLinkResults()
        err = self._cmd(udrv.CC_ESTABLISH_LINK, elp, elr)

        if not err:
            self.queryCCDInfo()

        return err

    def isLinked(self):
        # FIXME: ask SBIG to get a better CC_GET_LINK_STATUS.. this one it too bogus
        glsr = udrv.GetLinkStatusResults()
        self._cmd(udrv.CC_GET_LINK_STATUS, None, glsr)
        return bool(glsr.linkEstablished)

    def startExposure(self, ccd, exp_time, shutter):
        sep = udrv.StartExposureParams()

        sep.ccd = ccd
        sep.openShutter = shutter
        sep.abgState = 0
        sep.exposureTime = exp_time

        return self._cmd(udrv.CC_START_EXPOSURE, sep, None)

    def endExposure(self, ccd):
        eep = udrv.EndExposureParams()
        eep.ccd = ccd

        return self._cmd(udrv.CC_END_EXPOSURE, eep, None)

    def exposing(self, ccd):
        if ccd == self.imaging:
            return ((self._status(udrv.CC_START_EXPOSURE) & self._imgComplete) == self._imgInProgress)

        if ccd == self.tracking:
            return ((self._status(udrv.CC_START_EXPOSURE) & self._trkComplete) == self._trkInProgress)

    def startReadout(self, ccd, mode = 0, window = None):

        if mode not in self.readoutModes[ccd].keys():
            raise ValueError("Invalid readout mode")

        # geometry checking
        readoutMode = self.readoutModes[ccd][mode]

        window = (window or []) or readoutMode.getWindow()
        
        if (window[0] < 0 or window[0] > readoutMode.height):
            raise ValueError("Invalid window top point")

        if (window[1] < 0 or window[1] > readoutMode.width):
            raise ValueError("Invalid window left point")

        if (window[2] < 0 or window[2] > readoutMode.width):
            raise ValueError("Invalid window width")

        if (window[3] < 0 or window[3] > readoutMode.height):
            raise ValueError("Invalid window height")

        srp = udrv.StartReadoutParams()
        srp.ccd = ccd
        srp.readoutMode = mode
        srp.top    = window[0]
        srp.left   = window[1]
        srp.width  = window[2]
        srp.height = window[3]

        return self._cmd(udrv.CC_START_READOUT, srp, None)

    def endReadout(self, ccd):
        erp = udrv.EndReadoutParams()
        erp.ccd = ccd
        return self._cmd(udrv.CC_END_READOUT, erp, None)
    
    def readoutLine(self, ccd, mode = 0, line = None):

        if mode not in self.readoutModes[ccd].keys():
            raise ValueError("Invalid readout mode")

        # geometry check
        readoutMode = self.readoutModes[ccd][mode]

        line = line or readoutMode.getLine()

        if (line[0] < 0 or line[0] > readoutMode.width):
            raise ValueError("Invalid pixel start")
            
        if (line[1] < 0 or line[1] > readoutMode.width):
            raise ValueError("Invalid pixel lenght")

        rolp = udrv.ReadoutLineParams()
        rolp.ccd = ccd
        rolp.readoutMode = mode
        rolp.pixelStart = line[0]
        rolp.pixelLength = line[1]

        # create a numpy array to hold the line
        buff = numpy.zeros(line[1], numpy.uint16)

        self._cmd(udrv.CC_READOUT_LINE, rolp, buff)

        return buff

    # query and info functions

    def queryUSB(self):

        usb = udrv.QueryUSBResults()

        self._cmd(udrv.CC_QUERY_USB, None, usb)

        cams = []

        for cam in usb.usbInfo:
            if cam.cameraFound:
                cams.append(cam.name)

        return cams
    
    def queryDriverInfo(self):
        pass

    def queryCCDInfo(self):

        infoImg = udrv.GetCCDInfoResults0()
        infoTrk = udrv.GetCCDInfoResults0()

        gcip = udrv.GetCCDInfoParams()

        gcip.request = udrv.CCD_INFO_IMAGING
        self._cmd(udrv.CC_GET_CCD_INFO, gcip, infoImg)

        gcip.request = udrv.CCD_INFO_TRACKING
        self._cmd(udrv.CC_GET_CCD_INFO, gcip, infoTrk)

        # imaging ccd readout modes
        for i in range(infoImg.readoutModes):
            mode = infoImg.readoutInfo[i]
            self.readoutModes[self.imaging][mode.mode] = ReadoutMode(mode)

        for i in range(infoTrk.readoutModes):
            mode = infoTrk.readoutInfo[i]
            self.readoutModes[self.tracking][mode.mode] = ReadoutMode(mode)

        return True


    # temperature
    def setTemperature (self, regulation, setpoint, autofreeze = True):

        strp = udrv.SetTemperatureRegulationParams()

        if regulation == True:
            strp.regulation = udrv.REGULATION_ON
        else:
            strp.regulation = udrv.REGULATION_OFF
        
        strp.ccdSetpoint = TemperatureSetPoint.toAD (setpoint)

        self._cmd(udrv.CC_SET_TEMPERATURE_REGULATION, strp, None)

        # activate autofreeze if enabled
        if autofreeze == True:
            strp = udrv.SetTemperatureRegulationParams()
            strp.regulation = udrv.REGULATION_ENABLE_AUTOFREEZE
            return self._cmd(udrv.CC_SET_TEMPERATURE_REGULATION, strp, None)

        return True

    def getTemperature (self, ccd = True):
        """
	@returns: a tuple with (is cooling enabled, current cooling power (0-100), setpoint temperature, current ccd temperature)
	"""

        # USB based cameras have only one thermistor on the top of the CCD
        # Ambient thermistor value will be always 25.0 oC

        # ccdSetPoint value will be always equal to ambient thermistor
        # when regulation not enabled (not documented)

        qtsr = udrv.QueryTemperatureStatusResults()

        self._cmd (udrv.CC_QUERY_TEMPERATURE_STATUS, None, qtsr)

        return (qtsr.enabled,
                (qtsr.power / 255.0) * 100.0,
                TemperatureSetPoint.toDegrees(qtsr.ccdSetpoint, "ccd"),
                TemperatureSetPoint.toDegrees(qtsr.ccdThermistor, "ccd"))

    def startFan(self):
        mcp = udrv.MiscellaneousControlParams()
        mcp.fanEnable = 1
        return self._cmd(udrv.CC_MISCELLANEOUS_CONTROL, mcp, None)

    def stopFan(self):
        mcp = udrv.MiscellaneousControlParams()
        mcp.fanEnable = 0
        return self._cmd(udrv.CC_MISCELLANEOUS_CONTROL, mcp, None)

    def isFanning(self):
        status = self._status(udrv.CC_MISCELLANEOUS_CONTROL)
        return (status & 0x8)

    # filter wheel
    def getFilterPosition (self):
        cfwp = udrv.CFWParams()
        cfwp.cfwModel   = udrv.CFWSEL_CFW8
        cfwp.cfwCommand = udrv.CFWC_QUERY

        cfwr = udrv.CFWResults()

        self._cmd (udrv.CC_CFW, cfwp, cfwr)

        return cfwr.cfwPosition

    def setFilterPosition (self, position):
        cfwp = udrv.CFWParams()
        cfwp.cfwModel = udrv.CFWSEL_CFW8
        cfwp.cfwCommand = udrv.CFWC_GOTO
        cfwp.cfwParam1 = position

        cfwr = udrv.CFWResults()

        return self._cmd (udrv.CC_CFW, cfwp, cfwr)

    def getFilterStatus (self):
        cfwp = udrv.CFWParams()
        cfwp.cfwModel = udrv.CFWSEL_CFW8
        cfwp.cfwCommand = udrv.CFWC_QUERY

        cfwr = udrv.CFWResults()

        self._cmd (udrv.CC_CFW, cfwp, cfwr)

        return cfwr.cfwStatus

    # low-level commands

    def _cmd(self, cmd, cin, cout):

        err = udrv.SBIGUnivDrvCommand(cmd, cin, cout)

        if err == udrv.CE_NO_ERROR:
            return True
        else:
            log.error('Got a problem here! Dumping error params')
            gesp = udrv.GetErrorStringParams()
            gesr = udrv.GetErrorStringResults()

            gesp.errorNo = err
            
            udrv.SBIGUnivDrvCommand(udrv.CC_GET_ERROR_STRING, gesp, gesr)
            
            #dumpObj(gesp)
            #dumpObj(gesr)
            
            #log.warning('You may need to restart the SBIGDriver!')

            raise SBIGException(err, gesr.errorString)

    def _status(self, cmd):

        qcsp = udrv.QueryCommandStatusParams()
        qcsr = udrv.QueryCommandStatusResults()
        qcsp.command = cmd

        if not self._cmd(udrv.CC_QUERY_COMMAND_STATUS, qcsp, qcsr):
            return False

        return qcsr.status
