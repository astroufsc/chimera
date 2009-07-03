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

from chimera.interfaces.telescope import (TelescopeSlew, TelescopeSync,
                                          TelescopePark, TelescopeTracking,
                                          SlewRate)

from chimera.core.lock import lock

from chimera.util.simbad import Simbad


__all__ = ["TelescopeBase"]


class TelescopeBase(ChimeraObject,
                    TelescopeSlew, TelescopeSync,
                    TelescopePark, TelescopeTracking):

    def __init__(self):
        ChimeraObject.__init__(self)

        self._park_position = None
        
    @lock
    def slewToObject(self, name):
        simbad = Simbad()
        target = simbad.lookup(name)
        self.slewToRaDec(target)

    @lock
    def slewToRaDec(self, position):
        raise NotImplementedError()
       
    @lock
    def slewToAltAz(self, position):
        raise NotImplementedError()

    def abortSlew(self):
        raise NotImplementedError()

    def isSlewing(self):
        raise NotImplementedError()

    @lock
    def moveEast(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveWest(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveNorth(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveSouth(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveOffset(self, offsetRA, offsetDec, rate=SlewRate.GUIDE):

        if offsetRA == 0 :
            pass
        elif offsetRA > 0 :
            self.moveEast(offsetRA, rate)
        else:
            self.moveWest(abs(offsetRA), rate)

        if offsetDec == 0 :
            pass
        elif offsetDec > 0 :
            self.moveNorth(offsetDec, rate)
        else:
            self.moveSouth(abs(offsetDec), rate)

    def getRa(self):
        raise NotImplementedError()

    def getDec(self):
        raise NotImplementedError()

    def getAz(self):
        raise NotImplementedError()

    def getAlt(self):
        raise NotImplementedError()

    def getPositionRaDec(self):
        raise NotImplementedError()

    def getPositionAltAz(self):
        raise NotImplementedError()

    def getTargetRaDec(self):
        raise NotImplementedError()

    def getTargetAltAz(self):
        raise NotImplementedError()

    @lock
    def syncObject(self, name):
        simbad = Simbad()
        target = simbad.lookup(name)
        self.syncRaDec(target)

    @lock
    def syncRaDec(self, position):
        raise NotImplementedError()

    @lock
    def park(self):
        raise NotImplementedError()

    @lock
    def unpark(self):
        raise NotImplementedError()

    def isParked (self):
        raise NotImplementedError()

    @lock
    def setParkPosition(self, position):
        self._park_position = position

    def getParkPosition(self):
        return self._park_position or self["default_park_position"]

    def startTracking (self):
        raise NotImplementedError()

    def stopTracking (self):
        raise NotImplementedError()

    def isTracking (self):
        raise NotImplementedError()
        
    def getMetadata(self, request):
        return [('TELESCOP', self['model'], 'Telescope Model'),
                ('OPTICS',   self['optics'], 'Telescope Optics Type'),
                ('MOUNT', self['mount'], 'Telescope Mount Type'),
                ('APERTURE', self['aperture'], 'Telescope aperture size [mm]'),
                ('F_LENGTH', self['focal_length'], 'Telescope focal length [mm]'),
                ('F_REDUCT', self['focal_reduction'], 'Telescope focal reduction'),
                #TODO: Convert coordinates to proper equinox
                #TODO: How to get ra,dec at start of exposure (not end)
                ('RA', self.getRa().toHMS().__str__(), 'Right ascension of the observed object'),
                ('DEC', self.getDec().toDMS().__str__(), 'Declination of the observed object'),
                ("EQUINOX", 2000.0, "coordinate epoch"),
                ('ALT', self.getAlt().toDMS().__str__(), 'Altitude of the observed object'),
                ('AZ', self.getAz().toDMS().__str__(),'Azimuth of the observed object'),
                ("WCSAXES", 2, "wcs dimensionality"),
                ("RADESYS", "ICRS", "frame of reference"),
                ("CRVAL1", self.getTargetRaDec().ra.D, "coordinate system value at reference pixel"),
                ("CRVAL2", self.getTargetRaDec().dec.D, "coordinate system value at reference pixel"),
                ("CTYPE1", 'RA---TAN', "name of the coordinate axis"),
                ("CTYPE2", 'DEC---TAN', "name of the coordinate axis"),
                ("CUNIT1", 'deg', "units of coordinate value"),
                ("CUNIT2", 'deg', "units of coordinate value")]

