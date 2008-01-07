

from chimera.core.chimeraobject  import ChimeraObject

class ManagerHelperWithStopException (ChimeraObject):
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):    
        return True

    def __stop__ (self):
        raise Exception("oops in __stop__")

    def __main__ (self):
        return True
    
    def foo (self):
        return 42
    
