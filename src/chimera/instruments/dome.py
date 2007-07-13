#! /usr/bin/python
# -*- coding: iso8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  Antonio Kanaan <kanaan@astro.ufsc.br>

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
import sys

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.dome import IDome
from chimera.core.event import event
from chimera.core.async import lock

class Dome(BasicLifeCycle, IDome):

     def __init__(self, manager):
          BasicLifeCycle.__init__(self, manager)

          self._lastTelAz = None
          self._newTelAz = None

     def init(self, config):

          self.config += config

          # adjust timeslice
          self.timeslice = 1./self.config.time_res

          self.drv = self.manager.getDriver(self.config.driver)
          if not self.drv:
               logging.debug("Couldn't load selected driver (%s)." %  self.config.driver)
               return False

          self.tel = self.manager.getInstrument(self.config.telescope)
          if not self.tel:
               logging.warn ("Couldn't found a telescope. Dome will stay static.")
          
          return True

     def control (self):

          if not self.tel:
               return

          if (self.config.mode == "track"):

               self._newTelAz = self.tel.getAz()

               if not self._lastTelAz or (abs(self._newTelAz - self._lastTelAz) > self.config.az_res):
                    print "Moving dome to %s" % self._newTelAz
                    sys.stdout.flush ()
                    self.slewToAz(self._newTelAz)
                    print "Dome stopped"
                    sys.stdout.flush ()

               self._lastTelAz = self._newTelAz


     # -- IDomeSlew implementation
     @lock
     def track(self):
          self.config.mode = "track"

     @lock
     def stand(self):
          self.config.mode = "stand"

     def slewToAz (self, az):

        az = int (az)
          
        if az > 360:
             az = az % 360

        return self.drv.slewToAz (az)

     def isSlewing (self):
          return self.drv.isSlewing ()
    
     #def abortSlew (self):
     #     return self.drv.abortSlew ()

     def getAz (self):
          return self.drv.getAz ()

     def slitOpen (self):
          return self.drv.slitOpen ()

     def slitClose (self):
          return self.drv.slitClose ()

     # the variable domeFlatAzimuth needs to be globally defined
     # or it could be defined for the telescope and the dome could get it
     # from the telescope
     #def domeFlat (self):
     #     domeFlatAzimuth = 45
     #     slewToAz (self, domeFlatAzimuth)



