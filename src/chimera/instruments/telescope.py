#! /usr/bin/python
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


from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.telescope import ITelescopeSlew, ITelescopePark, ITelescopeSync

class Telescope(ChimeraObject, ITelescopeSlew, ITelescopePark, ITelescopeSync):

    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.drv = None

    def __init__(self):
        
        self.drv = self.getManager().getProxy(self['driver'])
        
        if not self.drv:
            self.log.warning("Couldn't found a driver. '%s' is not valid." % self['driver'])
            return False
    
        return True
    
    def __start__(self):
        try:
            self.drv.open();
        except TelescopeNotFoundException, e:
            self.log.exception(e)

    def __stop__(self):
        try:
            self.drv.close()
        except TelescopeNotFoundException, e:
            self.log.exception(e)

    def slewToObject(self, name):
        return ITelescopeSlew.slewToObject(self, name)


    def slewToRaDec(self, ra, dec, epoch="J2000"):
        return ITelescopeSlew.slewToRaDec(self, ra, dec, epoch)


    def slewToAzAlt(self, az, alt):
        return ITelescopeSlew.slewToAzAlt(self, az, alt)


    def abortSlew(self):
        return ITelescopeSlew.abortSlew(self)


    def isSlewing(self):
        return ITelescopeSlew.isSlewing(self)


    def moveEast(self, offset, rate=SlewRate.MAX):
        return ITelescopeSlew.moveEast(self, offset, rate)


    def moveWest(self, offset, rate=SlewRate.MAX):
        return ITelescopeSlew.moveWest(self, offset, rate)


    def moveNorth(self, offset, rate=SlewRate.MAX):
        return ITelescopeSlew.moveNorth(self, offset, rate)


    def moveSouth(self, offset, rate=SlewRate.MAX):
        return ITelescopeSlew.moveSouth(self, offset, rate)


    def getRa(self):
        return ITelescopeSlew.getRa(self)


    def getDec(self):
        return ITelescopeSlew.getDec(self)


    def getAz(self):
        return ITelescopeSlew.getAz(self)


    def getAlt(self):
        return ITelescopeSlew.getAlt(self)


    def getPosition(self):
        return ITelescopeSlew.getPosition(self)


    def getTarget(self):
        return ITelescopeSlew.getTarget(self)


    def slewStart(self, target):
        return ITelescopeSlew.slewStart(self, target)


    def slewComplete(self, position):
        return ITelescopeSlew.slewComplete(self, position)


    def abortComplete(self, position):
        return ITelescopeSlew.abortComplete(self, position)


    def syncRaDec(self, ra, dec):
        return ITelescopeSync.syncRaDec(self, ra, dec)


    def syncObject(self, name):
        return ITelescopeSync.syncObject(self, name)


    def syncComplete(self, position):
        return ITelescopeSync.syncComplete(self, position)


    def park(self):
        return ITelescopePark.park(self)


    def unpark(self):
        return ITelescopePark.unpark(self)


    def setParkPosition(self, az, alt):
        return ITelescopePark.setParkPosition(self, az, alt)


    def parkComplete(self):
        return ITelescopePark.parkComplete(self)


    def unparkComplete(self):
        return ITelescopePark.unparkComplete(self)


