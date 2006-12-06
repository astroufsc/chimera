#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.lifecycle import BasicLifeCycle
from uts.core.event import event

from uts.interfaces.camera import ICameraExpose

class Camera(BasicLifeCycle, ICameraExpose):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):
        self.drv = None

    # methods
    def expose (self, config):
        #self.drv.expose(config)
        pass
    
    def abortExposure (self, readout = True):
        #self.drv.abortExposure(readout)
        pass
