"""
The module implementation is a poor man's attempt at a singleton
pattern; at least we know no other camera driver can run within
this interpreter w/o a Vimba error.
"""
import time
import pymba as pb
import numpy as np

# Initialize the Vimba system
vimba = pb.Vimba()
vimba.startup()
# get system object
system = vimba.getSystem()


def list_cameras():
    # list available cameras (after enabling discovery for GigE cameras
    if system.GeVTLIsPresent:
        system.runFeatureCommand("GeVDiscoveryAllOnce")
        time.sleep(0.2)
    cameraIds = vimba.getCameraIds()
    for cId in cameraIds:
        print 'Camera ID:', cId


def get_camfeatures():
    # get and open a camera
    camera0 = vimba.getCamera(cameraIds[0])
    camera0.openCamera()

    # list camera features
    cameraFeatureNames = camera0.getFeatureNames()
    for name in cameraFeatureNames:
        print 'Camera feature:', name


def set_camfeature():
    # get the value of a feature
    print camera0.AcquisitionMode

    # set the value of a feature
    camera0.AcquisitionMode = 'SingleFrame'


def get_frames(mode='raw'):
    # create new frames for the camera
    frame0 = cam0.getFrame()    # creates a frame
    frame1 = cam0.getFrame()    # creates a second frame

    # announce frame
    frame0.announceFrame()

    # capture a camera image
    cam0.startCapture()
    frame0.queueFrameCapture()
    cam0.runFeatureCommand('AcquisitionStart')
    cam0.runFeatureCommand('AcquisitionStop')
    frame0.waitFrameCapture()

    # get image data
    if mode == 'raw':
        imgdata = frame0.getBufferByteData()
    else:
        imgdata = np.ndarray(buffer=frame0.getBufferByteData(),
                             dtype=np.uint8,
                             shape=(frame0.height, frame0.width, 1))

    return imgdata


def close_and_shutdown():
    # clean up after capture
    cam0.endCapture()
    cam0.revokeAllFrames()

    # close camera
    cam0.closeCamera()
    # shutdown Vimba
    vmb.shutdown()
