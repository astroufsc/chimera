#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

class ReadoutMode(object):

    def __init__(self, mode):
        self.mode =  mode.mode
        self.gain = float(hex(mode.gain).split('x')[1]) / 100.0
        self.width = mode.width
        self.height = mode.height
        self.pixelWidth = float(hex(mode.pixel_width).split('x')[1]) / 100.0
        self.pixelHeight = float(hex(mode.pixel_height).split('x')[1]) / 100.0

    def getSize(self):
        return (self.height, self.width)

    def getWindow(self):
        return [0, 0, self.width, self.height]

    def getLine(self):
        return [0, self.width]

    def __str__(self):
        return "%d: %.2f [%d,%d] [%.2f, %.2f]" % (self.mode, self.gain,
                                                  self.width, self.height,
                                                  self.pixelWidth, self.pixelHeight)
    

    def __repr__(self):
        return self.__str__()


class TemperatureSetpoint(object):

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
        
        r = cls.r0 * math.exp ( (math.log (cls.r_ratio[sensor]) * (cls.t0 - temp)) / cls.dt[sensor])

        setpoint = (cls.max_ad / ( (cls.r_bridge[sensor] / r) + 1.0 )) + 0.5

        #print "from %f to %d" % (temp, int(setpoint))

        return int(setpoint)

    @classmethod
    def toDegrees (cls, setpoint, sensor = "ccd"):

        if sensor not in ["ccd", "amb"]:
            sensor = "ccd"

        setpoint = int (setpoint)

        # limits from CSBIGCam
        if setpoint < 1:
            setpoint = 1
        elif setpoint >= (cls.max_ad - 1):
            setpoint = cls.max_ad - 1

        r = cls.r_bridge[sensor] / ( (float(cls.max_ad) / setpoint) - 1.0 )

        temp = cls.t0 - ( cls.dt[sensor] * ( math.log (r/cls.r0) / math.log (cls.r_ratio[sensor]) ) )

        #print "from %f to %f" % (setpoint, temp)

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

    filter_1 = udrv.CFWP_1
    filter_2 = udrv.CFWP_2
    filter_3 = udrv.CFWP_3
    filter_4 = udrv.CFWP_4
    filter_5 = udrv.CFWP_5

    # private
    _imgIdle       = 0x0
    _imgInProgress = 0x2
    _imgComplete   = 0x3
    _trkIdle       = 0x0
    _trkInProgress = 0x8
    _trkComplete   = 0xc

    def __init__(self):
        #FIXME: check device permissions and module status

        self._errorNo = 0
        self._errorString = ""

    def openDriver(self):

        ret = self._cmd(udrv.CC_OPEN_DRIVER, None, None)

        if not ret:
            err= self.getError ()

            # driver already open (are you trying to use the tracking ccd?)
            if err[0] == 21:
                return True
            else:
                self.setError (*err)
                return False

        return True

    def closeDriver(self):
        return self._cmd(udrv.CC_CLOSE_DRIVER, None, None)

    def openDevice(self, device):

        odp = udrv.OpenDeviceParams()
        odp.deviceType = device

        ret = self._cmd(udrv.CC_OPEN_DEVICE, odp, None)

        if not ret:
            err= self.getError ()

            # device already open (are you trying to use the tracking ccd?)
            if err[0] == 29:
                return True
            else:
                self.setError (*err)
                return False

        return True
        

    def closeDevice(self):
        return self._cmd(udrv.CC_CLOSE_DEVICE, None, None)

    def establishLink(self):
        elp = udrv.EstablishLinkParams()
        elr = udrv.EstablishLinkResults()

        return self._cmd(udrv.CC_ESTABLISH_LINK, elp, elr)

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
            self.setError(-1, "Invalid readout mode")
            return False

        # geometry checking
        readoutMode = self.readoutModes[ccd][mode]

        window = window or readoutMode.getWindow()
        
        if (window[0] < 0 or window[0] > readoutMode.height):
            self.setError(-1, "Invalid window top point")
            return False

        if (window[1] < 0 or window[1] > readoutMode.width):
            self.setError(-1, "Invalid window left point")
            return False

        if (window[2] < 0 or window[2] > readoutMode.width):
            self.setError(-1, "Invalid window width")
            return False

        if (window[3] < 0 or window[3] > readoutMode.height):
            self.setError(-1, "Invalid window height")
            return False

        srp = udrv.StartReadoutParams()
        srp.ccd = ccd
        srp.readoutMode = mode
        srp.top    = window[0]
        srp.left   = window[1]
        srp.height = window[2]
        srp.width  = window[3]

        return self._cmd(udrv.CC_START_READOUT, srp, None)

    def endReadout(self, ccd):
        erp = udrv.EndReadoutParams()

        erp.ccd = ccd

        return self._cmd(udrv.CC_END_READOUT, erp, None)
    
    def readoutLine(self, ccd, mode = 0, line = None):

        if mode not in self.readoutModes[ccd].keys():
            self.setError(-1, "Invalid readout mode")
            return False

        # geometry check
        readoutMode = self.readoutModes[ccd][mode]

        line = line or readoutMode.getLine()

        if (line[0] < 0 or line[0] > readoutMode.width):
            self.setError(-1, "Invalid pixel start")
            return False
            
        if (line[1] < 0 or line[1] > readoutMode.width):
            self.setError(-1, "Invalid pixel lenght")
            return False

        rolp = udrv.ReadoutLineParams()
        rolp.ccd = ccd
        rolp.readoutMode = mode
        rolp.pixelStart = line[0]
        rolp.pixelLength = line[1]

        # create a numpy array to hold the line
        buff = numpy.zeros(line[1], numpy.ushort)

        if not self._cmd(udrv.CC_READOUT_LINE, rolp, buff):
            return False

        return buff

    # query and info functions

    def queryUSB(self):

        usb = udrv.QueryUSBResults()

        if not self._cmd(udrv.CC_QUERY_USB, None, usb):
            return False

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
        if not self._cmd(udrv.CC_GET_CCD_INFO, gcip, infoImg):
            return False

        gcip.request = udrv.CCD_INFO_TRACKING
        if not self._cmd(udrv.CC_GET_CCD_INFO, gcip, infoTrk):
            return False

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
        
        strp.ccdSetpoint = TemperatureSetpoint.toAD (setpoint)

        ret = self._cmd(udrv.CC_SET_TEMPERATURE_REGULATION, strp, None)

        if not ret:
            return False

        # activate autofreeze if enabled
        if autofreeze == True:
            strp = udrv.SetTemperatureRegulationParams()
            strp.regulation = udrv.REGULATION_ENABLE_AUTOFREEZE
            strp.ccdSetpoint = 0 # irrelevant
            
            return self._cmd(udrv.CC_SET_TEMPERATURE_REGULATION, strp, None)

        return True

    def getTemperature (self, ccd = True):

        # USB based cameras have only one thermistor on the top of the CCD
        # Ambient thermistor value will be always 25.0 oC

        # ccdSetpoint value will be always equal to ambient thermistor when regulation not enabled (not documented)

        qtsr = udrv.QueryTemperatureStatusResults()

        ret = self._cmd (udrv.CC_QUERY_TEMPERATURE_STATUS, None, qtsr)

        if not ret:
            return False

        return (qtsr.enabled,
                (qtsr.power / 255.0) * 100.0,
                TemperatureSetpoint.toDegrees(qtsr.ccdSetpoint, "ccd"),
                TemperatureSetpoint.toDegrees(qtsr.ccdThermistor, "ccd"))

    # filter wheel
    def getFilterPosition (self):
        cfwp = udrv.CFWParams()
        cfwp.cfwModel = udrv.CFWSEL_CFW8
        cfwp.cfwCommand = udrv.CFWC_QUERY

        cfwr = udrv.CFWResults()

        ret = self._cmd (udrv.CC_CFW, cfwp, cfwr)

        if not ret:
            return -1

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

        ret = self._cmd (udrv.CC_CFW, cfwp, cfwr)

        if not ret:
            return False

        return cfwr.cfwStatus

    # low-level commands

    def setError(self, errorNo, errorString):
        self._errorNo = errorNo
        self._errorString = errorString

    def getError(self):
        if self._errorNo:
            ret = (self._errorNo, self._errorString)
        else:
            ret = 0

        self._errorNo = 0
        self._errorString = ""

        return ret

    def _cmd(self, cmd, cin, cout):
        err = udrv.SBIGUnivDrvCommand(cmd, cin, cout)

        if err == udrv.CE_NO_ERROR:
            return True
        else:
            gesp = udrv.GetErrorStringParams()
            gesr = udrv.GetErrorStringResults()

            gesp.errorNo = err
            
            udrv.SBIGUnivDrvCommand(udrv.CC_GET_ERROR_STRING, gesp, gesr)

            self.setError(err, gesr.errorString)

            return False

    def _status(self, cmd):

        qcsp = udrv.QueryCommandStatusParams()
        qcsr = udrv.QueryCommandStatusResults()
        qcsp.command = cmd

        if not self._cmd(udrv.CC_QUERY_COMMAND_STATUS, qcsp, qcsr):
            return False

        return qcsr.status

if __name__ == '__main__':

    import time

    s = SBIGDrv()
    t1 = time.time()
    s.openDriver()
    s.openDevice(SBIGDrv.usb)
    s.establishLink()
    t2 = time.time()

    print t2 - t1

    
    
