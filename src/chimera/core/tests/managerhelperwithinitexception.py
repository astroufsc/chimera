

from chimera.core.chimeraobject  import ChimeraObject

class ManagerHelperWithInitException (ChimeraObject):
    
    def __init__ (self):
        ChimeraObject.__init__(self)

        raise Exception("oops in __init__")
    
    def __start__ (self):
        return True
    
    def foo (self):
        return 42
    
