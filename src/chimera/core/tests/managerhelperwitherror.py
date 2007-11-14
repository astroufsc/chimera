

from chimera.core.chimeraobject  import ChimeraObject

class ManagerHelperWithError (ChimeraObject):
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):
        # start must return an true value to proceed.
        return False
    
    def foo (self):
        return 42
    
