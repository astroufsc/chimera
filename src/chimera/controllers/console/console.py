
from chimera.core.lifecycle import BasicLifeCycle
from chimera.controllers.console.commander import Commander

class Console (BasicLifeCycle):

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.console = None

    def init(self, config):
        self.config += config
        
        self.console = Commander (self)
        return True

    def shutdown (self):
        self.console.quit()
        return True

    def main (self):
        self.console.cmdloop ()
        Site().shutdown()
