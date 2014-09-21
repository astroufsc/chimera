from chimera.core.interface import Interface

from chimera.util.enum import Enum


AlignMode = Enum("ALT_AZ", "POLAR", "LAND")
SlewRate = Enum("GUIDE", "CENTER", "FIND", "MAX")


class Guider(Interface):
    __config__ = {"telescope": "/Telescope/0",
                  "camera": "/Camera/0",
                  "guidercamera": "/ChimeraGuider/0",
                  "gdr_filterwheel": "/FilterWheel/0",
                  "gdr_focuser": "/Focuser/focuser0",
                  "gdr_saveimages": False,
                  "gdr_imagesdir": "~/images",
                  "gdr_exptime": 1.0,
                  "gdr_filter": "R",
                  "maxwindows": 10,
                  "max_trials": 5
                  }
