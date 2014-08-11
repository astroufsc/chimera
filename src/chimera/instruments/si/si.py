import logging
from chimera.interfaces.camera import (CCD,
                                       Bitpix,
                                       Shutter,
                                       Camera,
                                       CameraFeature,
                                       CameraStatus,
                                       CameraExpose,
                                       CameraInformation,
                                       ReadoutMode,
                                       CameraTemperature)
from chimera.instruments.si.sidrv import SIDrv
from chimera.core.event import event
from chimera.core.exceptions import ChimeraException

log = logging.getloggger('chimera')


class SI():
    __config__ = {"device": "Ethernet",
                  "ccd": CCD.IMAGING,
                  "temp_delta": 2.0,
                  "ccd_saturation_level": 60000,
                  "camera_model": "Spectral Instruments Inc. 1110S",
                  "ccd_model": "TBD",
                  "telescope_focal_length": 4000  # milimeter
                  }

    def __init__(self):
        """
        Initialize the camera by asking for its driver
        """
        try:
            self.drv = SIDrv()
        except:
            log.critical("No camera available")
            exit()

    def __start__(self):
        """
        Fill in initial camera status with what the server
        knows. All future incquiries will go to the camera.
        """
        regs = self.drv.get_SGLII_settings()[1][6:]
        self.exptime = regs[0]
        self.nreadouts = regs[1]
        self.readoutmode = regs[2]
        self.navgimg = regs[3]
        self.nframes = regs[4]
        self.acqmode = regs[5]
        self.acqtype = regs[6]
        self.x1 = regs[7]
        self.width = regs[8]
        self.xbin = regs[9]
        self.y1 = regs[10]
        self.height = regs[11]
        self.ybin = regs[12]

    def getSize(self):
        return (self.width, self.height)

    def getWindow(self):
        return [0, 0, self.width, self.height]

    def getPixelSize(self):
        return (self.pixelWidth, self.pixelHeight)

    def getLine(self):
        return [0, self.width]

    def expose(self, request=None, **kwargs):
        pass

    def abortExposure(self, readout=True):
        pass

    def isExposing(self):
        pass

    @event
    def exposeBegin(self, request):
        pass

    @event
    def exposeComplete(self, request, status):
        pass

    @event
    def readoutBegin(self, request):
        pass

    @event
    def readoutComplete(self, proxy, status):
        pass

    def startCooling(self, tempC):
        pass

    def stopCooling(self):
        pass

    def isCooling(self):
        pass

    def getTemperature(self):
        pass

    def getSetPoint(self):
        pass

    def startFan(self, rate=None):
        pass

    def stopFan(self):
        pass

    def isFanning(self):
        pass

    @event
    def temperatureChange(self, newTempC, delta):
        pass

    def getCCDs(self):
        pass

    def getCurrentCCD(self):
        pass

    def getBinnings(self):
        pass

    def getADCs(self):
        pass

    def getPhysicalSize(self):
        pass

    def getPixelSize(self):
        pass

    def getOverscanSize(self):
        pass

    def getReadoutModes(self):
        pass

    def supports(self, feature=None):
        pass
