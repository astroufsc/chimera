from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.fan import FanControl


class FanBase(ChimeraObject, FanControl):
    def __init__(self):
        ChimeraObject.__init__(self)

    def switchOn(self):
        raise NotImplementedError

    def switchOff(self):
        raise NotImplementedError

    def isSwitchedOn(self):
        raise NotImplementedError
