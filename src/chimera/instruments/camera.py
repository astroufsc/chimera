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

from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.camera import ICameraExpose, ICameraTemperature

import logging

class Camera(ChimeraObject, ICameraExpose, ICameraTemperature):

    def __init__(self):
        ChimeraObject.__init__(self)

    def __init__ (self):
        self.drv = None
        return True

    def __start__ (self):

        self.drv = self.getProxy(self['driver'])

        try:
            self.drv.ping()

            # connect our callbacks
            
            
            
        except ObjectNotFoundException, e:
            
            return False
            

            
    def __stop__ (self):

        # disconnect our callbacks

        pass

    def expose (self, exptime,
                repeat=1, interval=0.0,
                shutter=Shutter.OPEN,
                binning=Binning.1x1,
                window="FULL_FRAME",
                filename="$date-$sequence.fits"):

        pass

    def abortExposure (self, readout=True):
        pass
    
    def isExposing (self):
        pass
    
    def startCooling (self, tempC):
        pass

    def stopCooling (self):
        pass
    
    def setTemperature(self, tempC):
        pass

    def getTemperature(self):
        pass
