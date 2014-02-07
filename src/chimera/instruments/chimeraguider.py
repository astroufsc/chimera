import threading
import time
import os
import datetime as dt

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event
from chimera.core.managerlocator import ManagerLocator


class CameraGuider(ChimeraObject):
    __config__ = {"telescope": "/Telescope/0",
                  "camera": "/Camera/0",
                  "filterwheel": "/FilterWheel/0",
                  "tolra": 0.0166666666667,
                  "toldec": 0.0166666666667,
                  "exptime": 10.0,
                  "filter": "V",
                  "max_trials": 5}

    def __init__(self):

        ChimeraObject.__init__(self)

    # Where is my telescope?
    def getTelescope(self):
        """
        Get the telescope we are guiding either from the __config__
        or from the running Manager, if needed. The latter should
        take precedence if different from the former (possible?).
        """
        pass


    def correctTelPos(self, pos):
        """
        Send direction and distance (in arcseconds?) to the telescope
        for correction, if the guiding algorithm does not deliver them
        directly (hence this method might prove unnecessary, except for
        decoupling).
        @param pos: list of tuples (dir, dist); e.g.:
        [('S', 1.2), ('E', 0.4)]
        Constraints:
        - At most 2 elements in the list;
        - Cannot have opposing cardinals: N-S, or E-W.
        """
        pass

    def getCorrections(self):
        """
        Here goes the meat, the meddle, the mothership...

        """
        pass

