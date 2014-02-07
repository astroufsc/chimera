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
