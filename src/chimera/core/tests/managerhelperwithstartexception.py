

from chimera.core.chimeraobject  import ChimeraObject

class ManagerHelperWithStartException (ChimeraObject):
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):

        raise Exception("oops in __start__")
    
        return True
    
    def foo (self):
        return 42
    
