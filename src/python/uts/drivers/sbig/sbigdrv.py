import sbigudrv as udrv
import numpy

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
        return self._cmd(udrv.CC_OPEN_DRIVER, None, None)

    def closeDriver(self):
        return self._cmd(udrv.CC_CLOSE_DRIVER, None, None)

    def openDevice(self, device):

        odp = udrv.OpenDeviceParams()
        odp.deviceType = device

        return self._cmd(udrv.CC_OPEN_DEVICE, odp, None)

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
            return ((self._status(udrv.CC_START_EXPOSURE) & self._trkComplete) == self._trkInProgress0)

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

    
    
