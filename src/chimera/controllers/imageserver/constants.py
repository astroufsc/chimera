#FIXME: Is this really necessary? All we're doing is cropping the image.
#       The amount of time saved by not reading out the entire chip is 
#       very probably not worth the effort in code.
#WINDOW values -- pre-cropping the readout area; not really necessary as image may be cropped later.
WINDOW_FULL         = (0.5, 0.5, 1.0, 1.0)
WINDOW_TOP_HALF     = (0.5, 0.25, 1.0, 0.5)
WINDOW_BOTTOM_HALF  = (0.5, 0.75, 1.0, 0.5)

Window      = {'FULL':          WINDOW_FULL,
               'TOP_HALF':      WINDOW_TOP_HALF,
               'BOTTOM_HALF':   WINDOW_BOTTOM_HALF}


#Since binning options are device dependent, let's have an addition to the camera driver interface:
#TODO: Add getBinningModes() method to camera driver interface
#      Returns: dictionary with keys being the human-readable string describing the binning mode
#      and the values being a device-specific constant that tells the device what binning to use
#BINNING_1X1 = (1, 1)
#BINNING_2X2 = (2, 2)
#BINNING_3X3 = (3, 3)
#BINNING_9X9 = (9, 9)
#BINNING_1X2 = (1, 2)
#BINNING_1X3 = (1, 3)
#BINNING_1X9 = (1, 9)
#BINNING_2X1 = (2, 1)
#BINNING_3X1 = (3, 1)
#BINNING_9X1 = (9, 1)