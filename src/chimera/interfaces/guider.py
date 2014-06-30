from chimera.core.interface import Interface

from chimera.util.enum import Enum


AlignMode = Enum("ALT_AZ", "POLAR", "LAND")
SlewRate =  Enum("GUIDE", "CENTER", "FIND", "MAX")


class Guider(Interface):
    __config__ = {"telescope":       "/Telescope/0",      # Telescope this guider will drive
                  "camera":          "/Camera/0",         # Main imaging camera
                  "guidercamera":    "/ChimeraGuider/0",  # Guider camera (might be one and the same)
                  "gdr_filterwheel": "/FilterWheel/0",    # As name suggests, if present
                  "gdr_focuser":     "/Focuser/focuser0", # Guider focusing mechanism
                  "gdr_saveimages":   False,              # Save gdr frames into fits files (MEF?)
                  "gdr_imagesdir":    "~/images",         # Where to save them if enabled
                  "gdr_exptime":      1.0,                # Fastest cadence, or
                  "gdr_filter":       "R",                # ...
                  "maxwindows":       10,                 # Number of guiding boxes
                  "max_trials":       5}                  # How many times to try guiding
