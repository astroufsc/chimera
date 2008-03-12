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


import threading

from chimera.core.methodwrapper  import MethodWrapper, MethodWrapperDispatcher


__all__ = ['LockWrapper',
           'LockWrapperDispatcher']


class LockWrapper (MethodWrapper):

    def __init__ (self, func, specials = None, dispatcher = None):
        MethodWrapper.__init__(self, func, specials, dispatcher)

        # this lock isn't marshalled as LockWrapper is local only
        # (remote user use Proxy which doesn't deal with locks, 'cause we do!)
        self.lock = threading.Lock()


class LockWrapperDispatcher (MethodWrapperDispatcher):   

    def __init__ (self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__ (self, wrapper, instance, cls)

    def call (self, *args, **kwargs):

        self.wrapper.lock.acquire()

        ret = None
        
        try:
            ret = self.func(*args, **kwargs)
        finally:
            self.wrapper.lock.release()

        return ret
