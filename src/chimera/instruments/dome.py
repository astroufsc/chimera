#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>
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
import Queue

from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.dome import IDome
from chimera.interfaces.dome import Mode

from chimera.core.event    import event
from chimera.core.lock     import lock
from chimera.core.callback import callback

from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.exceptions import ChimeraException

from chimera.util.coord import Coord


__all__ = ['Dome']


class Dome(ChimeraObject, IDome):

     def __init__(self):
          ChimeraObject.__init__(self)

          self.queue = Queue.Queue()

          self._lastTelAz = 0
          self._newTelAz  = 0

          self._mode = None

     def __start__(self):

          # connect events with driver
          drv = self.getDriver()
          drv.ping()
         
          drv.slewBegin     += self.getProxy()._slewBeginClbk
          drv.slewComplete  += self.getProxy()._slewCompleteClbk
          drv.abortComplete += self.getProxy()._abortCompleteClbk
          drv.slitOpened    += self.getProxy()._slitOpenedClbk
          drv.slitClosed    += self.getProxy()._slitClosedClbk

          self.setHz(0.5)

          if self["mode"] == Mode.Track:
               self.track ()
          elif self["mode"] == Mode.Stand:
               self.stand ()
          else:
               self.log.warning ("Invalid dome mode: %s. Will use Stand mode instead.")
               self.stand ()

          # telescope events
          try:
               tel = self.getTelescope()

               tel.slewBegin     += self.getProxy()._telSlewBeginClbk
               tel.slewComplete  += self.getProxy()._telSlewCompleteClbk
               tel.abortComplete += self.getProxy()._telAbortCompleteClbk

          except ObjectNotFoundException:
               self.log.warning("Couldn't found telescope."
                                "Telescope events would not be monitored.")

          return True

     def __stop__ (self):
          # disconnect events
          drv = self.getDriver()
         
          drv.slewBegin     -= self.getProxy()._slewBeginClbk
          drv.slewComplete  -= self.getProxy()._slewCompleteClbk
          drv.abortComplete -= self.getProxy()._abortCompleteClbk
          drv.slitOpened    -= self.getProxy()._slitOpenedClbk
          drv.slitClosed    -= self.getProxy()._slitClosedClbk

          try:
               tel = self.getTelescope()
               
               tel.slewBegin     -= self.getProxy()._telSlewBeginClbk
               tel.slewComplete  -= self.getProxy()._telSlewCompleteClbk
               tel.abortComplete -= self.getProxy()._telAbortCompleteClbk

          except ObjectNotFoundException:
               pass

          return True

     # callbacks
     def _slewBeginClbk(self, position):
          if not isinstance(position, Coord):
               position = Coord.fromDMS(position)

          self.slewBegin(position)
          
     def _slewCompleteClbk(self, position):
          if not isinstance(position, Coord):
               position = Coord.fromDMS(position)

          self.slewComplete(position)

     def _abortCompleteClbk(self, position):
          if not isinstance(position, Coord):
               position = Coord.fromDMS(position)

          self.abortComplete(position)

     def _slitOpenedClbk(self, position):
          if not isinstance(position, Coord):
               position = Coord.fromDMS(position)

          self.slitOpened(position)

     def _slitClosedClbk(self, position):
          if not isinstance(position, Coord):
               position = Coord.fromDMS(position)

          self.slitClosed(position)

     # telescope callbacks
     def _telSlewBeginClbk (self, target):
          if self.getMode() != Mode.Track: return

          # FIXME: conversao equatorial-local
          #self.queue.put(target.asAzAlt(site.longitude(), site.lst()))

     def _telSlewCompleteClbk (self, target):
          if self.getMode() != Mode.Track: return

          tel = self.getTelescope()
          self.queue.put(tel.getAz())

     def _telAbortCompleteClbk (self, position):
          if self.getMode() != Mode.Track: return

          tel = self.getTelescope()
          self.queue.put(tel.getAz())

     @lock
     def getDriver(self):
          return self.getManager().getProxy(self['driver'], lazy=True)        
        
     @lock
     def getTelescope(self):
          return self.getManager().getProxy(self['telescope'], lazy=True)        

     def control (self):

          drv = self.getDriver()

          if self.getMode() != Mode.Track:
               return True

          if not self.queue.empty():
               self._processQueue()
               return True

          return True

          try:
               tel = self.getTelescope()

               self._newTelAz = tel.getAz()

               if (abs(self._newTelAz - self._lastTelAz) >= drv["az_resolution"]):
                    self.slewToAz(self._newTelAz)

               self._lastTelAz = self._newTelAz

          except ObjectNotFoundException:
               raise ChimeraException("Couldn't found the selected telescope."
                                      " Dome cannnot track.")

          return True
     
     def _processQueue (self):
          
          if self.queue.empty(): return

          target = self.queue.get()

          self.slewToAz(target)
          self.queue.task_done()
          
     @lock
     def track(self):
          self._mode = Mode.Track

          tel = self.getTelescope()
          self.queue.put(tel.getAz())

     @lock
     def stand(self):
          self._mode = Mode.Stand          

     def getMode(self):
          return self._mode

     def slewToAz (self, az):

          if not isinstance(az, Coord):
               az = Coord.fromDMS(az)

          if int(az) >= 360:
               az = az % 360
          
          drv = self.getDriver()
          drv.slewToAz (az)

     def isSlewing (self):
          return self.drv.isSlewing ()
    
     def abortSlew (self):
          # FIXME
          drv = self.getDriver()
          drv.abortSlew ()

     def getAz (self):
          drv = self.getDriver()
          return drv.getAz ()

     def openSlit (self):
          drv = self.getDriver()
          drv.openSlit()

     def closeSlit (self):
          drv = self.getDriver()
          drv.closeSlit()

     def isSlitOpen (self):
          drv = self.getDriver()
          return drv.isSlitOpen()

