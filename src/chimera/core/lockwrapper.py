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


import logging
import time

from chimera.core.methodwrapper  import MethodWrapper, MethodWrapperDispatcher

from chimera.core.constants      import INSTANCE_MONITOR_ATTRIBUTE_NAME

import chimera.core.log
log = logging.getLogger(__name__)


__all__ = ['LockWrapper',
           'LockWrapperDispatcher']


class LockWrapper (MethodWrapper):

    def __init__ (self, func, specials = None, dispatcher = None):
        MethodWrapper.__init__(self, func, specials, dispatcher)


class LockWrapperDispatcher (MethodWrapperDispatcher):   

    def __init__ (self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__ (self, wrapper, instance, cls)

    def call (self, *args, **kwargs):
        """
        Locked or synchronized methods holds two locks. The object
        monitor, which gives exclusive right to run locked methods and
        the object configuration writer lock, which gives exclusive
        right to read/write config values.
        """

        lock = getattr(self.instance, INSTANCE_MONITOR_ATTRIBUTE_NAME)

        t0 = time.time()
        #log.debug("[trying to acquire monitor] %s %s" % (self.instance, self.func.__name__))
        lock.acquire()
        #log.debug("[acquired monitor] %s %s after %f" % (self.instance, self.func.__name__, time.time()-t0))        

        ret = None
        
        try:
            ret = self.func(*args, **kwargs)
        finally:
            #log.debug("[release monitor] %s %s" % (self.instance, self.func.__name__))
            lock.release()

        return ret
