from chimera.interfaces.camera import (Camera,
                                       CCD,
                                       CameraFeature,
                                       CameraExpose,
                                       CameraInformation,
                                       CameraStatus,
                                       CameraTemperature,
                                       ReadoutMode)
from chimera.core.event import event
from chimera.core.exceptions import NotImplementedException
import avtdrvmod


class AVTGigE(Camera, ReadoutMode, CameraExpose, CameraTemperature, CameraInformation):

    def __init__(self):
        """
        Initialize the GenTL interface, goes out to discover devices via GVCP.
        @return:
        """
        pass

    def __start__(self):
        """
        Initialize the camera driver and GenTL interface
        """
        pass

    # These methods will plug onto the GenICam ImageFormatControl Node.
    #
    def getSize(self):
        """
        Queries the relevant __config__ values, which may have been updated from
        the camera's registers via GenICam, at __start__ time.
        @return: (width, height) tuple.
        """
        pass

    def getWindow(self):
        """
        Idem
        @return:[0, 0, width, height] list.
        """
        pass

    def getPixelSize(self):
        pass

    def getLine(self):
        pass

    # These methods will plug onto the GenICam AcquisitionControl Node.
    #
    def expose(self, request=None, **kwargs):
        """
        TBD!!!
        @param kwargs: image exposure parameters, if not coming from ImageRequest (likely)
        @return:
        """
        pass

    def abortExposure(self, readout=False):
        """
        Stops the ongoing exposure
        @param readout: whether to save the partially exposed frame
        @return: True if successful, False otherwise.
        """
        pass

    def isExposing(self):
        """
        Is it? This consults the camera's status via GC file or event?
        @return: True|False
        """
        pass

    # These methods will plug onto the GenICam EventAcquisitionStartData Node.
    #
    @event
    def exposeBegin(self, **kwargs):
        """
        Start the guiding exposures.
        @param kwargs:
        @return:
        """
        pass

    def readoutBegin(self):
        pass

    # These methods will plug onto the GenICam EventAcquisitionEndData Node.
    #
    def exposeComplete(self):
        pass

    def readoutComplete(self):
        pass

    # These methods will plug onto the GenICam DeviceControl Node.
    #
    def getTemperature(self):
        pass

    def isFanning(self):
        pass

    def temperatureChange(self):
        """
        This can probably be taken from the GenICam events functionality
        @return:
        """
        pass

    def getCCDs(self):
        """
        Returns the __config__ value
        @return: string
        """
        pass

    # AFAIK, all these have no implementation on the camera...
    #
    def startCooling(self):
        raise NotImplementedException()

    def stopCooling(self):
        raise NotImplementedException()

    def isCooling(self):
        raise NotImplementedException()

    def getSetPoint(self):
        pass

    def startFan(self):
        raise NotImplementedException()

    def stopFan(self):
        raise NotImplementedException()

    def getCurrentCCD(self):
        raise NotImplementedException()

    def getBinnings(self):
        """
        From __config__ updated from GenICam?
        @return: dict of possible values.
        """
        pass

    def getADCs(self):
        pass

    def getPhysicalSize(self):
        pass

    def getOverscanSize(self):
        raise NotImplementedException()

    def getReadoutModes(self):
        pass

    def supports(self):
        pass
