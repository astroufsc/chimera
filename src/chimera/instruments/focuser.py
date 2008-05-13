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
from chimera.interfaces.focuser import IFocuser

from chimera.core.lock import lock


class Focuser (ChimeraObject, IFocuser):

    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):

        drv = self.getDriver()
        drv.ping()

        return True

    def getDriver(self):
        """
        Get a Proxy to the instrument driver. This function is necessary '
        cause Proxies cannot be shared among different threads.
        So, every time you need a driver Proxy you need to call this to
        get a Proxy to the current thread.
        """
        return self.getManager().getProxy(self['driver'], lazy=True)        

    @lock
    def moveIn (self, n):
        drv = self.getDriver()
        drv.moveIn (n)

    @lock
    def moveOut (self, n):
        drv = self.getDriver()
        drv.moveOut (n)

    @lock
    def moveTo (self, position):
        drv = self.getDriver()
        drv.moveTo (position)
    
    def getPosition (self):
        drv = self.getDriver()
        return drv.getPosition ()
