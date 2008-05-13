
from chimera.core.chimeraobject import ChimeraObject

from chimera.controllers.console.commander import Commander

class Console (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)

        self.console = None

    def __start__ (self):
        self.console = Commander (self)
        return True

    def __stop__ (self):
        self.console.quit()
        return True

    def __main__ (self):
        self.console.cmdloop()
