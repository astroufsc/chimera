#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

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

import time
import threading

from chimera.interfaces.telescope  import SlewRate, TelescopeStatus
from chimera.instruments.telescope import TelescopeBase

from chimera.core.lock import lock
from chimera.core.site import Site

from chimera.util.coord    import Coord
from chimera.util.position import Position, Epoch


class FakeTelescope (TelescopeBase):
    
    def __init__ (self):
        TelescopeBase.__init__(self)

        self.__slewing = False
        self._az  = Coord.fromDMS(0)
        self._alt = Coord.fromDMS(70)

        self._slewing  = False
        self._tracking = True
        self._parked   = False
        
        self._abort = threading.Event()
        
        try:
            self._site = self.getManager().getProxy("/Site/0")
            self._gotSite=True
        except:
            self._site = Site()
            self._gotSite=False
        
        self._setRaDecFromAltAz()
    
    def _getSite(self):
        if self._gotSite:
            self._site._transferThread()
            return self._site
        else:
            try:
                self._site = self.getManager().getProxy("/Site/0")
                self._gotSite=True
            except:
                pass
        return self._site
    
    def _setRaDecFromAltAz(self):
        raDec=self._getSite().altAzToRaDec(Position.fromAltAz(self._alt, self._az))
        self._ra=raDec.ra
        self._dec=raDec.dec

    def _setAltAzFromRaDec(self):
        altAz=self._getSite().raDecToAltAz(Position.fromRaDec(self._ra, self._dec))
        self._alt=altAz.alt
        self._az=altAz.az

    def __start__ (self):
        self.setHz(1)

    @lock
    def control (self):
        self._getSite()
        if not self._slewing:
            if self._tracking:
                self._setAltAzFromRaDec()
            else:
                self._setRaDecFromAltAz()                                                          
        return True

    def slewToRaDec(self, position):

        if not isinstance(position, Position):
            position = Position.fromRaDec(position[0], position[1], epoch=Epoch.J2000)

        position_now = self._getFinalPosition(position)

        self.slewBegin(position_now)

        ra_steps = position_now.ra - self.getRa()
        ra_steps = float(ra_steps/10.0)

        dec_steps = position_now.dec - self.getDec()
        dec_steps = float(dec_steps/10.0)

        self._slewing = True
        self._abort.clear()

        status = TelescopeStatus.OK

        t = 0
        while t < 5:

            if self._abort.isSet():
                self._slewing = False
                status = TelescopeStatus.ABORTED
                break

            self._ra  += ra_steps
            self._dec += dec_steps
            self._setAltAzFromRaDec()
            
            time.sleep(0.5)
            t += 0.5
        
        self._slewing = False
            
        self.slewComplete(self.getPositionRaDec(), status)

    @lock
    def slewToAltAz(self, position):

        if not isinstance(position, Position):
            position = Position.fromAltAz(*position)

        self.slewBegin(self._getSite().altAzToRaDec(position))

        alt_steps = position.alt - self.getAlt()
        alt_steps = float(alt_steps/10.0)

        az_steps = position.az - self.getAz()
        az_steps = float(az_steps/10.0)

        self._slewing = True
        self._abort.clear()

        status = TelescopeStatus.OK
        t = 0
        while t < 5:

            if self._abort.isSet():
                self._slewing = False
                status = TelescopeStatus.ABORTED
                break

            self._alt  += alt_steps
            self._az += az_steps
            self._setRaDecFromAltAz()
            
            time.sleep(0.5)
            t += 0.5
        
        self._slewing = False
            
        self.slewComplete(self.getPositionRaDec(), status)

    def abortSlew(self):
        self._abort.set()
        while self.isSlewing():
            time.sleep(0.1)

    def isSlewing (self):
        return self._slewing

    @lock
    def moveEast(self, offset, rate=SlewRate.MAX):

        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra + Coord.fromAS(offset), pos.dec)
        self.slewBegin(pos)
        
        self._ra += Coord.fromAS(offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveWest(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra + Coord.fromAS(-offset), pos.dec)
        self.slewBegin(pos)
        
        self._ra += Coord.fromAS(-offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveNorth(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra, pos.dec + Coord.fromAS(offset))
        self.slewBegin(pos)
        
        self._dec += Coord.fromAS(offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveSouth(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra, pos.dec + Coord.fromAS(-offset))
        self.slewBegin(pos)
        
        self._dec += Coord.fromAS(-offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def getRa(self):
        return self._ra

    @lock
    def getDec(self):
        return self._dec

    @lock
    def getAz(self):
        return self._az

    @lock
    def getAlt(self):
        return self._alt

    @lock
    def getPositionRaDec(self):
        return Position.fromRaDec(self.getRa(), self.getDec())

    @lock
    def getPositionAltAz(self):
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def getTargetRaDec(self):
        return Position.fromRaDec(self.getRa(), self.getDec())

    @lock
    def getTargetAltAz(self):
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def syncRaDec (self, position):
        if not isinstance(position, Position):
            position = Position.fromRaDec(*position)

        self._ra = position.ra
        self._dec = position.dec

    @lock
    def park(self):
        self.log.info("Parking...")
        self._parked = True
        self.parkComplete()

    @lock
    def unpark(self):
        self.log.info("Unparking...")
        self._parked = False
        self.unparkComplete()        

    def isParked(self):
        return self._parked

    @lock
    def startTracking (self):
        self._tracking = True

    @lock
    def stopTracking (self):
        self._tracking = False

    def isTracking (self):
        return self._tracking
