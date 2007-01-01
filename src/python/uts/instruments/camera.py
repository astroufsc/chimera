#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.lifecycle import BasicLifeCycle
from uts.core.event import event

from uts.interfaces.camera import ICameraExpose

import logging

class Camera(BasicLifeCycle, ICameraExpose):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):

        self.config += config

        self.drv = self.manager.getDriver(self.config.driver)

        if not self.drv:
            logging.debug("Couldn't load selected driver (%ss). Will use the default (Fake)" %  self.config.driver)
            self.drv = self.manager.getDriver("/Fake/camera")

    # methods
    def expose (self, config):

        def expose_cb ():
            self.exposeComplete ()

        def readout_cb ():
            self.readoutComplete ()

        self.drv.exposeComplete += expose_cb
        self.drv.readoutComplete += readout_cb
        
        self.drv.expose(config)
        return True

    def abortExposure (self, config):

        def abort_cb ():
            self.exposeAborted ()
            
        self.drv.exposeAborted += abort_cb

        return self.drv.abortExposure(config)

    def exposing (self):
        return self.drv.exposing () 
