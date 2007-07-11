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

import logging
import time

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.telescope import ITelescopeSlew

class Telescope(BasicLifeCycle, ITelescopeSlew):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):

        self.config += config

        self.drv = self.manager.getDriver(self.config.driver)

        if not self.drv:
            logging.debug("Couldn't load selected driver (%s)." %  self.config.driver)
            return False

        #self.drv.slewComplete += self._slew_cb
        #self.drv.abortComplete += self._abort_cb

        return True


    # callbacks

    def _slew_cb (self, position):
        self.slewComplete (position)

    def _abort_cb (self, position):
        self.abortComplete (position)

    # -- ITelescopeSlew implementation
    
    def slewToRaDec (self, ra, dec):
        return self.drv.slewToRaDec (ra, dec)

    def slewToAzAlt (self, az, alt):
        return self.drv.slewToAzAlt (az, alt)

    def isSlewing (self):
        return self.drv.isSlewing ()
    
    def moveEast (self, offset):
        return self.drv.moveEast (offset)        

    def moveWest (self, offset):
        return self.drv.moveWest (offset)        

    def moveNorth (self, offset):
        return self.drv.moveNorth (offset)        

    def moveSouth (self, offset):
        return self.drv.moveSouth (offset)        

    def abortSlew (self):
        return self.drv.abortSlew ()

    def getRa (self):
        return self.drv.getRa ()
    
    def getDec (self):
        return self.drv.getDec ()
    
    def getAz (self):
        return self.drv.getAz ()
    
    def getAlt (self):
        return self.drv.getAlt ()
    
    def getPosition (self):
        return self.drv.getPosition ()
    
    def getTarget (self):
        return self.drv.getTarget ()
    
    
