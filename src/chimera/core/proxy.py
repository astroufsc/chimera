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


try:
    import Pyro.core
except ImportError, e:
    raise RuntimeError ("You must have Pyro version >= 3.6 installed.")

from chimera.core.remoteobject import RemoteObject
from chimera.core.constants    import MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT
from chimera.core.constants    import EVENTS_PROXY_NAME, EVENTS_ATTRIBUTE_NAME
from chimera.core.constants    import METHODS_ATTRIBUTE_NAME
from chimera.core.location     import Location

import chimera.core.log
import logging


__all__ = ['Proxy',
           'ProxyMethod']


log = logging.getLogger(__name__)

           
class Proxy (Pyro.core.DynamicProxy):

    def __init__ (self, location = None, host=None, port=None, uri = None):
        Pyro.core.initClient (banner=0)

        if not uri:
            location = Location(location)

            host = (host or location.host) or MANAGER_DEFAULT_HOST
            port = (port or location.port) or MANAGER_DEFAULT_PORT
            
            uri = Pyro.core.PyroURI(host=host,
                                    port=port,
                                    objectID="/%s/%s" % (location.cls, location.name))
        
        Pyro.core.DynamicProxy.__init__ (self, uri)
        
    def ping (self):

        try:
            return self.__ping__ ()
        except Pyro.errors.ProtocolError, e:
            return 0

    def __getattr__ (self, attr):
        if attr == "__getinitargs__":
            raise AttributeError()
            
        return ProxyMethod(self, attr)

    def __iadd__ (self, configDict):
        ProxyMethod(self, "__iadd__")(configDict)
        return self

    def __repr__ (self):
        return "<%s proxy at %s>" % (self.URI, hex(id(self)))

    def __str__ (self):
        return "[proxy for %s]" % self.URI


class ProxyMethod (object):

    def __init__ (self, proxy, method):

        self.proxy  = proxy
        self.method = method
        self.sender = self.proxy._invokePYRO

        self.__name__ = method

    def __repr__ (self):
        return "<%s.%s method proxy at %s>" % (self.proxy.URI,
                                               self.method,
                                               hex(hash(self)))

    def __str__ (self):
        return "[method proxy for %s %s method]" % (self.proxy.URI,
                                                    self.method)

    # synchronous call, just call method using our sender adapter
    def __call__ (self, *args, **kwargs):
        return self.sender (self.method, args, kwargs)

    # async pattern
    def begin (self, *args, **kwargs):
        return self.sender ("%s.begin" % self.method, args, kwargs)

    def end (self, *args, **kwargs):
        return self.sender ("%s.end" % self.method, args, kwargs)

    # event handling

    def __do (self, other, action):

        handler = {"topic"    : self.method,
                   "handler"  : {"proxy" : "",
                                "method": ""}
                   }

        # REMEBER: Return a copy of this wrapper as we are using +=
        
        # Can't add itself as a subscriber
        if other == self:
            return self
        
        # passing a proxy method?
        if not isinstance (other, ProxyMethod):
            log.debug("Invalid parameter: %s" % other)
            raise TypeError("Invalid parameter: %s" % other)

        handler["handler"]["proxy"] = other.proxy.URI
        handler["handler"]["method"] = str(other.__name__)
   
        try:
            self.sender ("%s.%s" % (EVENTS_PROXY_NAME, action), (handler,), {})
        except Exception, e:
            log.exception("Cannot %s to topic '%s' using proxy '%s'." % (action,
                                                                         self.method,
                                                                         self.proxy))

        return self

    def __iadd__ (self, other):
        return self.__do (other, "subscribe")

    def __isub__ (self, other):
        return self.__do (other, "unsubscribe")


