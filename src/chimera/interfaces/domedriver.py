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


from chimera.core.interface import Interface
from chimera.core.event import event


class IDomeDriver (Interface):

    __config__ = {"device": "/dev/ttyS1",
                  "az_resolution": 2,  # dome position resolution in degrees
                  "slew_timeout" : 120,
                  "abort_timeout": 60,
                  "init_timeout" : 5,
                  "open_timeout" : 20,
                  "close_timeout": 20,
                  } 
  
    # methods

    def slewToAz (self, az):
        pass

    def isSlewing (self):
        pass

    def abortSlew (self):
        pass

    def openSlit (self):
        pass

    def closeSlit (self):
        pass

    def isSlitOpen (self):
        pass

    def getAz(self):
        pass

    # events
    
    @event
    def slewBegin (self, position):
        pass

    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass
    
    @event
    def slitOpened (self, az):
        pass

    @event
    def slitClosed (self, az):
        pass
