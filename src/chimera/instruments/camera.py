#! /usr/bin/python
# -*- coding: iso8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from chimera.core.lifecycle import BasicLifeCycle
from chimera.core.event import event

from chimera.interfaces.camera import ICameraExpose, ICameraTemperature

import logging

class Camera(BasicLifeCycle, ICameraExpose, ICameraTemperature):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):

        self.config += config

        self.drv = self.manager.getDriver(self.config.driver)

        if not self.drv:
            logging.debug("Couldn't load selected driver (%ss). Will use the default (Fake)" %  self.config.driver)
            self.drv = self.manager.getDriver("/Fake/camera")


        # connect events
        self.drv.exposeComplete += self.expose_cb
        self.drv.readoutComplete += self.readout_cb
        self.drv.exposeAborted += self.abort_cb
        self.drv.temperatureChanged += self.temp_cb

    # callbacks
    def expose_cb (self):
        self.exposeComplete ()

    def readout_cb (self):
        self.readoutComplete ()

    def abort_cb (self):
        self.exposeAborted ()

    def temp_cb (self, new, old):
        self.temperatureChanged (new, old)

    # methods
    def expose (self, config):
        return self.drv.expose(config)

    def abortExposure (self, config):
        return self.drv.abortExposure(config)

    def exposing (self):
        return self.drv.exposing ()

    def setTemperature(self, config):
        return self.drv.setTemperature (config)

    def getTemperature(self):
        return self.drv.getTemperature ()
    
