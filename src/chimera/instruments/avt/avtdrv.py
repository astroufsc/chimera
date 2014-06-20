import time
from pymba import *


class LittleRedThingy(object):

    def __init__(self):
        # start Vimba
        self.vimba = Vimba()
        self.vimba.startup()
        # get system object
        self.system = self.vimba.getSystem()

    def list_cameras(self):
        # list available cameras (after enabling discovery for GigE cameras)
        if self.system.GeVTLIsPresent:
            self.system.runFeatureCommand("GeVDiscoveryAllOnce")
            time.sleep(0.2)
        self.cameraIds = self.vimba.getCameraIds()
        for cId in self.cameraIds:
            print 'Camera ID:', cId

    def get_camfeatures(self):
        # get and open a camera
        self.camera0 = self.vimba.getCamera(cameraIds[0])
        self.camera0.openCamera()

        # list camera features
        cameraFeatureNames = self.camera0.getFeatureNames()
        for name in cameraFeatureNames:
            print 'Camera feature:', name

    def set_camfeature(self):
        # get the value of a feature
        print self.camera0.AcquisitionMode

        # set the value of a feature
        self.camera0.AcquisitionMode = 'SingleFrame'

    def get_frames(self, mode='raw'):
        # create new frames for the camera
        frame0 = self.cam0.getFrame()    # creates a frame
        frame1 = self.cam0.getFrame()    # creates a second frame

        # announce frame
        frame0.announceFrame()

        # capture a camera image
        self.cam0.startCapture()
        frame0.queueFrameCapture()
        self.cam0.runFeatureCommand('AcquisitionStart')
        self.cam0.runFeatureCommand('AcquisitionStop')
        frame0.waitFrameCapture()

        # get image data...
        if mode == 'raw':
            imgdata = frame0.getBufferByteData()
        else:
            imgdata = np.ndarray(buffer=frame0.getBufferByteData(),
                                 dtype=np.uint8,
                                 shape=(frame0.height,
                                        frame0.width,
                                        1))

        return imgdata

    def close_and_shutdown(self):
        # clean up after capture
        self.cam0.endCapture()
        self.cam0.revokeAllFrames()

        # close camera
        self.cam0.closeCamera()
        # shutdown Vimba
        self.vmb.shutdown()
