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


from chimera.core.proxy          import ProxyMethod
from chimera.core.methodwrapper  import MethodWrapperDispatcher

from chimera.core.constants import EVENTS_PROXY_NAME

import copy

__all__ = ['EventWrapperDispatcher']


class EventWrapperDispatcher (MethodWrapperDispatcher):   

    def __init__ (self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__ (self, wrapper, instance, cls)

    def call (self, *args, **kwargs):

        if hasattr(self.instance, EVENTS_PROXY_NAME):
            getattr(self.instance, EVENTS_PROXY_NAME).publish (self.func.__name__, *args[1:], **kwargs)

        return True

    def __do (self, other, action):

        handler = {"topic"    : self.func.__name__,
                   "handler"  : {"proxy" : "",
                                 "method": ""}}
        
        # REMEBER: Return a copy of this wrapper as we are using +=

        # Can't add itself as a subscriber
        if other == self.func:
            return copy.copy(self)
        
        # passing a proxy method?
        if not isinstance (other, ProxyMethod):
            return copy.copy(self)

        handler["handler"]["proxy"] = other.proxy.URI
        handler["handler"]["method"] = str(other.__name__)
   
        if hasattr(self.instance, EVENTS_PROXY_NAME):
            proxy = getattr(self.instance, EVENTS_PROXY_NAME)
            f = getattr(proxy, action)
            f(handler)

        return copy.copy(self)


    def __iadd__ (self, other):
        return self.__do (other, "subscribe")
        
    def __isub__ (self, other):
        return self.__do (other, "unsubscribe")
