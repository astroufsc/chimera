import logging
import time

from uts.core.lifecycle import BasicLifeCycle

class Sample(BasicLifeCycle):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)
            
    def init(self, config):

        # FIXME: automatic?
        self.config += config

        self.cam = self.manager.getInstrument('/Camera/st8')

        self.cam.exposeComplete += self.exposeComplete
        self.cam.readoutComplete += self.readoutComplete

        self.cam.expose({"exp_time": 100})

    def exposeComplete (self):
        print "tada!!!.. acabou de expor"

    def readoutComplete (self):
        print "tada!!!.. acabou de gravar"

    def shutdown(self):
        pass

    def control(self):
        pass

