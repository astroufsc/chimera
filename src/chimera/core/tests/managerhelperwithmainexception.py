

from chimera.core.chimeraobject  import ChimeraObject

class ManagerHelperWithMainException (ChimeraObject):
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):    
        return True

    def __main__ (self):
        raise Exception("oops in __main__")
    
    def foo (self):
        return 42
    
