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


from chimera.core.metaobject   import MetaObject
from chimera.core.remoteobject import RemoteObject

from chimera.core.config      import Config
from chimera.core.eventsproxy import EventsProxy

from chimera.core.state    import State
from chimera.core.location import Location

from chimera.interfaces.lifecycle import ILifeCycle

import chimera.core.log

import logging
import time
from types import StringType


__all__ = ['ChimeraObject']

    
class ChimeraObject (RemoteObject, ILifeCycle):

    __metaclass__ = MetaObject

    def __init__ (self):
        RemoteObject.__init__(self)
    
        # event handling
        self.__events_proxy__ = EventsProxy (self)

        # configuration handling
        self.__config_proxy__ = Config (self)

        self.__state__ = State.STOPPED

        self.__location__ = ""

        # logging
        self.log = logging.getLogger(self.__module__)

        # Hz
        self.controlFrequency = 2

    # config implementation
    def __getitem__ (self, item):
        return self.__config_proxy__.__getitem__ (item)
    
    def __setitem__ (self, item, value):
        return self.__config_proxy__.__setitem__ (item, value)

    # ILifeCycle implementation
    def __start__ (self):
        return True
        
    def __stop__ (self):
        return True

    def __main__ (self):

        runCondition = True

        while runCondition:
            runCondition = self.control()               
            time.sleep(1.0/self.controlFrequency)

        return True

    def control (self):
        return False

    def getState (self):
        return self.__state__

    def __setstate__ (self, state):
        oldstate = self.__state__
        self.__state__ = state
        return oldstate

    def getLocation (self):
        return self.__location__

    def __setlocation__ (self, location):

        l = Location(location)

        if not l.isValid():
            return False
        
        self.__location__ = location
        self.setGUID(str(location))
        return True

    def getManager (self):
        if self.getDaemon():
            return self.getDaemon().getManager()

    def getProxy (self):
        # just to put everthing together (no need to change the base implementation)
        return super(ChimeraObject, self).getProxy()
