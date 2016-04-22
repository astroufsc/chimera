from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.fan import FanControl


class FanBase(ChimeraObject, FanControl):
    def __init__(self):
        ChimeraObject.__init__(self)

    def startFan(self):
        raise NotImplementedError

    def stopFan(self):
        raise NotImplementedError

    def isFanRunning(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError