#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

from chimera.core.threads import getThreadPool

# FIXME: exception handling

class AsyncResult(object):

    def __init__(self, func, pool = None):

        self.func = func
        self.result = None
        self.userCallback = False

        self.waiting = False
        self.sleepTime = 0.1

        self.pool = pool or getThreadPool(10)

    def __call__(self, *args, **kwargs):
        logging.debug("calling synchronously %s with %s %s" % (self.func,
                                                               args, kwargs))

        if(hasattr(self.func, "lock")):
            self.func.lock.acquire()
            
        result = self.func(*args, **kwargs)

        if(hasattr(self.func, "lock")):
            self.func.lock.release()

        return result

    def begin(self, *args, **kwargs):
        logging.debug("calling asynchronously %s with %s %s" % (self.func,
                                                                args, kwargs))

        if(not self.pool):
            logging.error("Cannot run async calls, pool is not seted")
            return False

        self.userCallback = kwargs.pop('callback', None)
        self.waiting = True

        self.pool.queueTask(self.func, args, kwargs, self.resultCallback)

        return self

    def end(self):
        while (self.waiting):
            #wait
            time.sleep(self.sleepTime)

        return self.result

    def resultCallback(self, result):
        self.result = result
        self.waiting = False

        if(self.userCallback):
            self.userCallback(self.result)

