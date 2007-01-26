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
