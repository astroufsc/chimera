from chimera.core.interface  import Interface
from chimera.core.event      import event
from chimera.core.exceptions import ChimeraException

from chimera.util.enum import Enum


AlignMode = Enum("ALT_AZ", "POLAR", "LAND")
SlewRate  = Enum("GUIDE", "CENTER", "FIND", "MAX")

class Guider(Interface):
        # New config items:
    # maxwindows: the idea is to keep potential guiding targets from the
    # same field, just in case, to be able to quickly switch among them.
    # (easier said than done). TBD
    # guidercamera: the actual hardware guider we'll be driving.
    __config__ = {"telescope"       : "/Telescope/0",
                  "camera"          : "/Camera/0",
                  "guidercamera"    : "/Moravian/guiding",
                  "filterwheel"     : "/FilterWheel/0",
                  "savegdrimages"   : False,
                  "gdrimagesdir"    : "~/images",
                  "exptime"         : 1.0,
                  "filter"          : "V",
                  "maxwindows"      : 10,
                  "max_trials"      : 5}

