# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.metaobject import MetaObject
from chimera.core.config import Config
from chimera.core.proxy import Proxy

from chimera.core.state import State
from chimera.core.location import Location

from chimera.core.constants import EVENTS_ATTRIBUTE_NAME
from chimera.core.constants import METHODS_ATTRIBUTE_NAME
from chimera.core.constants import CONFIG_PROXY_NAME
from chimera.core.constants import INSTANCE_MONITOR_ATTRIBUTE_NAME
from chimera.core.constants import RWLOCK_ATTRIBUTE_NAME

from chimera.interfaces.lifecycle import ILifeCycle

import logging
import time
import threading


__all__ = ["ChimeraObject"]


class ChimeraObject(ILifeCycle, metaclass=MetaObject):

    def __init__(self):
        ILifeCycle.__init__(self)

        # configuration handling
        self.__config_proxy__ = Config(self)

        self.__state__ = State.STOPPED

        self.__location__: Location

        # logging.
        # put every logger on behalf of chimera's logger so
        # we can easily setup levels on all our parts
        logName = self.__module__
        if not logName.startswith("chimera."):
            logName = "chimera." + logName + f" ({logName})"

        self.log = logging.getLogger(logName)

        # Hz
        self._Hz = 2
        self._loop_abort = threading.Event()

        # To override metadata default values
        self.__metadataOverrideMethod__ = None

    # config implementation
    def __getitem__(self, item):
        # any thread can read if none writing at the time
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquireRead()
            return self.__config_proxy__.__getitem__(item)
        finally:
            lock.release()

    def __setitem__(self, item, value):
        # only one thread can write
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquireWrite()
            return self.__config_proxy__.__setitem__(item, value)
        finally:
            lock.release()

    # bulk configuration (pass a dict to config multiple values)
    def __iadd__(self, configDict):
        # only one thread can write
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquireWrite()
            self.__config_proxy__.__iadd__(configDict)
        finally:
            lock.release()
            return self.getProxy()

    # locking
    def __enter__(self):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).__enter__()

    def __exit__(self, *args):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).__exit__(*args)

    def acquire(self, blocking=True):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).acquire(blocking)

    def release(self):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).release()

    def wait(self, timeout=None):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).wait(timeout)

    def notify(self, n=1):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).notify(n)

    def notifyAll(self):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).notifyAll()

    # reflection
    def __get_events__(self):
        return getattr(self, EVENTS_ATTRIBUTE_NAME)

    def __get_methods__(self):
        return getattr(self, METHODS_ATTRIBUTE_NAME)

    def __get_config__(self):
        return list(getattr(self, CONFIG_PROXY_NAME).items())

    # ILifeCycle implementation
    def __start__(self):
        return True

    def __stop__(self):
        return True

    def getHz(self):
        return self._Hz

    def setHz(self, freq):
        tmpHz = self.getHz()
        self._Hz = freq
        return tmpHz

    def __main__(self):

        self._loop_abort.clear()
        timeslice = 0.01

        runCondition = True

        while runCondition:

            runCondition = self.control()

            if self._loop_abort.is_set():
                return True

            # FIXME: better idle loop
            # we can't sleep for the whole time because
            # if object set a long sleep time and Manager decides to
            # shutdown, we must be asleep to receive his message and
            # return.
            timeToWakeUp = 1.0 / self.getHz()
            slept = 0
            while slept < timeToWakeUp:
                time.sleep(timeslice)
                if self._loop_abort.is_set():
                    return True
                slept += timeslice

        return True

    def __abort_loop__(self):
        self._loop_abort.set()

    def control(self):
        return False

    def getState(self):
        return self.__state__

    def __setstate__(self, state):
        oldstate = self.__state__
        self.__state__ = state
        return oldstate

    def getLocation(self):
        return self.__location__

    def __setlocation__(self, location):
        self.__location__ = Location(location)
        return True

    def getManager(self):
        return Proxy(
            f"{self.__location__.host}:{self.__location__.port}/Manager/manager"
        )

    def getMetadata(self, request):
        # Check first if there is metadata from a metadata override method.
        md = self.getMetadataOverride(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        return []

    def setMetadataMethod(self, location):
        # Defines an alternative class to getMetadata()
        self.__metadataOverrideMethod__ = location

    def getMetadataOverride(self, request):
        # Returns metadata from the override class or None if there is no override getMetadata() class.
        if self.__metadataOverrideMethod__ is not None:
            return (
                self.getManager()
                .getProxy(self.__metadataOverrideMethod__)
                .getMetadata(request)
            )
        return None

    def features(self, interface):
        """
        Checks if self is an instance of an interface.
        This is useful to check if some interface/capability is supported by an instrument
        :param interface: One of from chimera interfaces
        :return: True if is instance, False otherwise
        """
        return isinstance(self, interface)

    def getProxy(self) -> Proxy:
        return Proxy(self.__location__)
