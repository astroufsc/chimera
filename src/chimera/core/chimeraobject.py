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

from chimera.core.constants import EVENTS_ATTRIBUTE_NAME
from chimera.core.constants import METHODS_ATTRIBUTE_NAME
from chimera.core.constants import CONFIG_PROXY_NAME

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
        self.__events_proxy__ = EventsProxy ()

        # configuration handling
        self.__config_proxy__ = Config (self)

        self.__state__ = State.STOPPED

        self.__location__ = ""

        # logging.
        # put every logger on behalf of chimera's logger so
        # we can easily setup levels on all our parts
        logName = self.__module__
        if not logName.startswith("chimera."):
            logName = "chimera."+logName+" (%s)" % logName

        self.log = logging.getLogger(logName)

        # Hz
        self._Hz = 2

    # config implementation
    def __getitem__ (self, item):
        return self.__config_proxy__.__getitem__ (item)
    
    def __setitem__ (self, item, value):
        return self.__config_proxy__.__setitem__ (item, value)

    # bulk configuration (pass a dict to config multiple values)
    def __iadd__ (self, configDict):
        self.__config_proxy__.__iadd__ (configDict)
        return self.getProxy()

    # reflection
    def __get_events__ (self):
        return getattr(self, EVENTS_ATTRIBUTE_NAME)

    def __get_methods__ (self):
        return getattr(self, METHODS_ATTRIBUTE_NAME)

    def __get_config__ (self):
        return getattr(self, CONFIG_PROXY_NAME).items()
    
    # ILifeCycle implementation
    def __start__ (self):
        return True
        
    def __stop__ (self):
        return True

    def getHz (self):
        return self._Hz

    def setHz (self, freq):
        tmpHz = self.getHz()
        self._Hz = freq
        return tmpHz

    def __main__ (self):

        runCondition = True

        while runCondition:
            runCondition = self.control()
            time.sleep(1.0/self.getHz())

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

        location = Location(location)

        self.__location__ = location
        self.setGUID("/%s/%s" % (location.cls, location.name))
        return True

    def getManager (self):
        if self.getDaemon():
            return self.getDaemon().getProxyForObj(self.getDaemon().getManager())

    def getProxy (self):
        # just to put everthing together (no need to change the base implementation)
        return super(ChimeraObject, self).getProxy()
