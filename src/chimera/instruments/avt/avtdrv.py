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

    def get_frames(self):
        # create new frames for the camera
        frame0 = camera0.getFrame()    # creates a frame
        frame1 = camera0.getFrame()    # creates a second frame

        # announce frame
        frame0.announceFrame()

        # capture a camera image
        camera0.startCapture()
        frame0.queueFrameCapture()
        camera0.runFeatureCommand('AcquisitionStart')
        camera0.runFeatureCommand('AcquisitionStop')
        frame0.waitFrameCapture()

        # get image data...
        imgData = frame0.getBufferByteData()
        return imgdata

        # ...or use NumPy for fast image display (for use with OpenCV, etc)
        #import numpy as np
        #moreUsefulImgData = np.ndarray(buffer = frame0.getBufferByteData(),
        #                               dtype = np.uint8,
        #                               shape = (frame0.height,
        #                                        frame0.width,
        #                                        1))

        # clean up after capture
        self.camera0.endCapture()
        self.camera0.revokeAllFrames()

        # close camera
        self.camera0.closeCamera()

    def shutdown(self):
        # shutdown Vimba
        self.vimba.shutdown()

