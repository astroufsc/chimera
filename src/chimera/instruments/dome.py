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
import threading

from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.dome import Dome, Mode

from chimera.core.lock    import lock

from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.exceptions import ChimeraException

from chimera.util.coord import Coord


__all__ = ['DomeBase']


class DomeBase (ChimeraObject, Dome):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.queue = Queue.Queue()
        self._mode = None

        # to reuse telescope proxy on control method
        self._tel = None
        self._telChanged = False

        # to cache for az_resolution of the dome
        self.controlAzRes = None

        self._waitAfterSlew = threading.Event()
        self._waitAfterSlew.clear()

    def __start__ (self):

        self.setHz(1/4.)

        tel = self.getTelescope()
        if tel:
            self._connectTelEvents()
        else:
            self.log.warning("Couldn't find telescope. Telescope events would"
                             " not be monitored. Dome will stay in Stand mode.")
            self["mode"] = Mode.Stand

        if self["mode"] == Mode.Track:
            self.track ()
        elif self["mode"] == Mode.Stand:
            self.stand ()
        else:
            self.log.warning ("Invalid dome mode: %s. "
                              "Will use Stand mode instead.")
            self.stand ()

        self.log.debug("Dome started in %s mode." % self.getMode())

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

        tel = self.getTelescope()
        if not tel:
            self.log.warning("Couldn't find telescope. Telescope events would"
                             " not be monitored. Dome will stay in Stand mode.")
            self['mode'] == Mode.Stand
            return False

        tel.slewBegin     += self.getProxy()._telSlewBeginClbk
        tel.slewComplete  += self.getProxy()._telSlewCompleteClbk
        return True

    def _disconnectTelEvents (self):

        tel = self.getTelescope()
        if tel:
            tel.slewBegin     -= self.getProxy()._telSlewBeginClbk
            tel.slewComplete  -= self.getProxy()._telSlewCompleteClbk
            return True
        return False

    def _reconnectTelEvents (self):
        self._disconnectTelEvents()
        self._connectTelEvents()

    # telescope callbacks
    def _telSlewBeginClbk (self, target):
        self.log.debug("[event] telescope slewing to %s." % target)
        
    def _telSlewCompleteClbk (self, target, status):
        self.log.debug("[event] telescope slew complete, position=%s status=%s." % (target, status))

    # utilitaries
    def getTelescope(self):
        try:
            p = self.getManager().getProxy(self['telescope'], lazy=True)
            if not p.ping():
                return False
            else:
                return p
        except ObjectNotFoundException:
            return False

    def control (self):

        if self.getMode() == Mode.Stand:
            return True

        if not self.queue.empty():
            self._processQueue()
            return True

        try:
            if not self._tel or self._telChanged:
                self._tel = self.getTelescope()
                self._telChanged = False
                if not self._tel: return True
                
            if self._tel.isSlewing():
                self.log.debug("[control] telescope slewing... not checking az.")
                self._waitAfterSlew.set()
                return True

            self._telescopeChanged(self._tel.getAz())
            # flag all waiting threads that the control loop already checked the new telescope position
            # probably adding new azimuth to the queue
            self._waitAfterSlew.clear()

        except ObjectNotFoundException:
            raise ChimeraException("Couldn't found the selected telescope."
                                   " Dome cannnot track.")

        return True

    def _telescopeChanged (self, az):

        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if self._needToMove(az):
            self.log.debug("[control] adding %s to the queue (delta=%.2f)" % (az, abs(self.getAz()-az)))
            self.queue.put(az)
        else:
            self.log.debug("[control] standing"
                           " (dome az=%.2f, tel az=%.2f, delta=%.2f.)" % (self.getAz(), az, abs(self.getAz()-az)))


    def _needToMove (self, az):
        return abs(az - self.getAz()) >= self["az_resolution"]

    def _processQueue (self):

        if self._waitAfterSlew.isSet():
            self._telescopeChanged(self._tel.getAz())

        if self.queue.empty(): return

        self.log.debug("[control] processing queue... %d item(s)." % self.queue.qsize())
            
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

        tel = self.getTelescope()
        
        if tel:
            self._reconnectTelEvents()
            self._telChanged = True
            self.log.debug("[mode] tracking...")
            self._telescopeChanged(tel.getAz())
            self._mode = Mode.Track
        else:
            self.log.warning("Could not contact the given telescope, staying in Stand mode.")

    @lock
    def stand(self):
        self._processQueue()
        self.log.debug("[mode] standing...")
        self._mode = Mode.Stand

    @lock
    def syncWithTel(self):
        self.syncBegin()

        if self.getMode() != Mode.Stand:
            self._telescopeChanged(self._tel.getAz())
            self._processQueue()

        self.syncComplete()

    @lock
    def isSyncWithTel(self):
        return self._needToMove(self._tel.getAz())

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
