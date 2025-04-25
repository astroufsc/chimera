from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.fan import FanControl


class FanBase(ChimeraObject, FanControl):
    def __init__(self):
        ChimeraObject.__init__(self)

    def switch_on(self):
        raise NotImplementedError

    def switch_off(self):
        raise NotImplementedError

    def is_switched_on(self):
        raise NotImplementedError
