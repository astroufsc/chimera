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

import Queue

from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.dome import (IDome, Mode)

from chimera.core.lock    import lock

from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.exceptions import ChimeraException

from chimera.util.coord import Coord


__all__ = ['DomeBase']


class DomeBase (ChimeraObject, IDome):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.queue = Queue.Queue()
        self._mode = None

        # to reuse telescope proxy on control method
        self._tel = None

        # to cache for az_resolution of the dome
        self.controlAzRes = None

    def __start__(self):

        self.setHz(1/4.0)

        tel = self.getTelescope()
        if tel:
            self._connectTelEvents()
        else:
            self["mode"] = Mode.Stand

        if self["mode"] == Mode.Track:
            self.track ()
        elif self["mode"] == Mode.Stand:
            self.stand ()
        else:
            self.log.warning ("Invalid dome mode: %s. "
                              "Will use Stand mode instead.")
            self.stand ()

        return True

    def __stop__ (self):

        if self['park_on_shutdown']:

            try:
                self.stand()
                self.log.info("Parking the dome...")
                self.slewToAz(self['park_position'])
            except Exception, e:
                self.log.warning('Unable to park dome: %s', str(e))

        if self['close_on_shutdown'] and self.isSlitOpen():
            try:
                self.log.info("Closing the slit...")
                self.closeSlit()
            except Exception, e:
                self.log.warning('Unable to close dome: %s', str(e))
        
        # telescope events
        self._disconnectTelEvents()
        return True

    def _connectTelEvents (self):
        
        try:
            tel = self.getTelescope()
            if not tel: return
            tel.slewBegin    += self.getProxy()._telSlewBeginClbk
            tel.slewComplete  += self.getProxy()._telSlewCompleteClbk
            tel.abortComplete += self.getProxy()._telAbortCompleteClbk

        except ObjectNotFoundException:
            self.log.warning("Couldn't found telescope."
                                "Telescope events would not be monitored.")

        return True

    def _disconnectTelEvents (self):
        try:
            tel = self.getTelescope()
            if not tel: return
            
            tel.slewBegin    -= self.getProxy()._telSlewBeginClbk
            tel.slewComplete  -= self.getProxy()._telSlewCompleteClbk
            tel.abortComplete -= self.getProxy()._telAbortCompleteClbk

        except ObjectNotFoundException:
            pass

        return True

    def _reconnectTelEvents (self):
        self._disconnectTelEvents()
        self._connectTelEvents()

    # telescope callbacks
    def _telSlewBeginClbk (self, target):
        if self.getMode() != Mode.Track: return

        self.log.debug("[event] telescope slewing to %s." % target)
        
    def _telSlewCompleteClbk (self, target):
        if self.getMode() != Mode.Track: return

        tel = self.getTelescope()
        self.log.debug("[event] telescope slew complete, "
                       "new position=%s." % target)

    def _telAbortCompleteClbk (self, position):
        if self.getMode() != Mode.Track: return

        tel = self.getTelescope()
        self.log.debug("[event] telescope aborted last slew, "
                       "new position=%s." % position)

    # utilitaries
    def getTelescope(self):
        p = self.getManager().getProxy(self['telescope'], lazy=True)
        if not p.ping(): return False
        return p

    def control (self):

        if self.getMode() == Mode.Stand:
            return True

        if not self.queue.empty():
            self.log.debug("[control] processing queue... %d item(s)." % self.queue.qsize())
            self._processQueue()
            return True

        try:

            if not self._tel:
                self._tel = self.getTelescope()

            if self._tel.isSlewing():
                    self.log.debug("[control] telescope slewing... not checking az.")
                    return True

            self._telescopeChanged(self._tel.getAz())

        except ObjectNotFoundException:
            raise ChimeraException("Couldn't found the selected telescope."
                                    " Dome cannnot track.")

        return True

    def _telescopeChanged (self, az):

        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if self._needToMove(az):
            self.log.debug("[control] adding %s to the queue." % az)
            self.queue.put(az)
        else:
            self.log.debug("[control] telescope still in the slit, standing"
                            " (dome az=%.2f, tel az=%.2f, delta=%.2f.)" % (self.getAz(), az, abs(self.getAz()-az)))


    def _needToMove (self, az):
        return abs(az - self.getAz()) >= self["az_resolution"]

    def _processQueue (self):
        
        if self.queue.empty(): return

        while not self.queue.empty():

            target = self.queue.get()
            try:
                self.log.debug("[queue] slewing to %s" % target)
                self.slewToAz(target)
            finally:
                self.log.debug("[queue] slew to %s complete" % target)                
                self.queue.task_done()
        
    @lock
    def track(self):
        if self.getMode() == Mode.Track: return

        self._reconnectTelEvents()
        
        tel = self.getTelescope()
        self.log.debug("[mode] tracking...")
        self._telescopeChanged(tel.getAz())

        self._mode = Mode.Track

    @lock
    def stand(self):
        self._processQueue()
        self.log.debug("[mode] standing...")
        self._mode = Mode.Stand

    @lock
    def syncWithTel(self):
        self._processQueue()

    @lock
    def isSyncWithTel(self):
        return self.queue.empty()

    def getMode(self):
        return self._mode

    @lock
    def slewToAz (self, az):
        raise NotImplementedError()
        
    def isSlewing (self):
        raise NotImplementedError()
    
    def abortSlew (self):
        raise NotImplementedError()

    @lock
    def getAz (self):
        raise NotImplementedError()

    @lock
    def openSlit (self):
        raise NotImplementedError()

    @lock
    def closeSlit (self):
        raise NotImplementedError()

    def isSlitOpen (self):
        raise NotImplementedError()
    
    def getMetadata(self, request):
        if self.isSlitOpen():
            slit = 'Open'
        else:
            slit = 'Closed'

        return [('DOME_MDL', str(self['model']), 'Dome Model'),
                ('DOME_TYP', str(self['style']), 'Dome Type'),
                ('DOME_TRK', str(self['mode']), 'Dome Tracking/Standing'),
                ('DOME_SLT', str(slit), 'Dome slit status')]
