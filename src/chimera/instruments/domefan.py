from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.domefan import DomeFan


class DomeFanBase(ChimeraObject, DomeFan):
    def __init__(self):
        ChimeraObject.__init__(self)

    def getRotation(self):
        raise NotImplementedError

    def setRotation(self, freq):
        raise NotImplementedError

    def getDirection(self):
        raise NotImplementedError

    def setDirection(self, direction):
        raise NotImplementedError

    def startFan(self):
        raise NotImplementedError

    def stopFan(self):
        raise NotImplementedError

    def isFanRunning(self):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError
