
from chimera.core.interface import Interface
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event
import time

class MinimoException (Exception):
    pass


class IMinimo (Interface):

    __config__ = {"option1": "value1",
                  "option2": "value2"}

    def doMethod (self, bar):
        pass

    def doEvent (self):
        pass

    def doRaise (self):
        pass

    @staticmethod
    def doStatic ():
        pass
    
    @classmethod
    def doClass (cls):
        pass

    @event
    def eventDone (self, result):
        pass


class Minimo (ChimeraObject, IMinimo):

    CONST = "Class method works!"

    def __init__(self):
        ChimeraObject.__init__ (self)

    def __start__ (self):
        self.log.info ("Minimo starting with option1=%s" % self["option1"])
        return True

    def __stop__ (self):
        self.log.info ("Minimo stopping")
        return True

    def control (self):
        self.log.info ("Minimo looping")
        return False # exit control loop

    def doMethod (self, bar):
        return "Method works!"

    def doEvent (self):
        self.eventDone("Event works!")

    def doRaise (self):
        raise MinimoException("Exception works!")

    @staticmethod
    def doStatic ():
        return "Static method works!"

    @classmethod
    def doClass (cls):
        return cls.CONST
        

