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
from chimera.interfaces.focuser import IFocuser

import logging

class Focuser (BasicLifeCycle, IFocuser):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):
        self.config += config

        self.drv = self.manager.getDriver(self.config.driver)

        if not self.drv:
            logging.debug("Couldn't load selected driver (%s)." %  self.config.driver)
            return False

        return True

    def moveIn (self, n):
        if not self.drv.moveIn (n):
            logging.warning (self.drv.getError()[1])
            return False

        return True

    def moveOut (self, n):
        if not self.drv.moveOut (n):
            logging.warning (self.drv.getError()[1])
            return False

        return True

    def moveTo (self, position):
        if not self.drv.moveTo (position):
            logging.warning (self.drv.getError()[1])
            return False

        return True

    def getPosition (self):
        ret = self.drv.getPosition ()

        if ret == -1:
            logging.warning (self.drv.getError()[1])
            return ret
    
        return ret
            
