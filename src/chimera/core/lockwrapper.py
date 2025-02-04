# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import logging

from chimera.core.methodwrapper import MethodWrapper, MethodWrapperDispatcher

from chimera.core.constants import INSTANCE_MONITOR_ATTRIBUTE_NAME

log = logging.getLogger(__name__)


__all__ = ["LockWrapper", "LockWrapperDispatcher"]


class LockWrapper(MethodWrapper):

    def __init__(self, func, specials=None, dispatcher=None):
        MethodWrapper.__init__(self, func, specials, dispatcher)


class LockWrapperDispatcher(MethodWrapperDispatcher):

    def __init__(self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        """
        Locked or synchronized methods holds two locks. The object
        monitor, which gives exclusive right to run locked methods and
        the object configuration writer lock, which gives exclusive
        right to read/write config values.
        """

        lock = getattr(self.instance, INSTANCE_MONITOR_ATTRIBUTE_NAME)

        # t0 = time.time()
        # log.debug("[trying to acquire monitor] %s %s" % (self.instance, self.func.__name__))
        lock.acquire()
        # log.debug("[acquired monitor] %s %s after %f" % (self.instance, self.func.__name__, time.time()-t0))

        ret = None

        try:
            ret = self.func(*args, **kwargs)
        finally:
            # log.debug("[release monitor] %s %s" % (self.instance, self.func.__name__))
            lock.release()

        return ret
