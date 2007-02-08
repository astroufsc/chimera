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

from uts.core.lifecycle import BasicLifeCycle

from uts.interfaces.telescope import ITelescopeSlew

class Telescope(BasicLifeCycle, ITelescopeSlew):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        #self.timeslice = 0.05 # 20 Hz
            
    def init(self, config):
        pass

    def shutdown(self):
        pass
        
    def inst_main(self):
        self.slewComplete("%.10f" % time.time(), "", "")
    
    def slew(self, coord):
        # parse and validate coord
        res = self.driver.slewToRaDec.begin((coord['ra'], coord['dec']), callback=self._slewComplete)
        return res.end()

    def isSlewing(self):
        res = self.driver.isSlewing.begin()
        return res.end()

    def abortSlew(self):
        res = self.driver.abortSlew.begin(callback=self._abortSlew)
        return res.end()

    def getRa(self):
        res = self.driver.getRa()
        return res

    def getDec(self):
        return 1000        

    def _slewComplete(self, status):
        # check status
        #if status = True:
        #   self.slewComplete(status['position'])
        logging.info("_slewComplete callback")

    def _abortSlew(self, status):
        #self.slewAborted()
        logging.info("_abortSlew callback")
