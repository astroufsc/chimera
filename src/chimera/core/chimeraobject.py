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
        log_name = self.__module__
        if not log_name.startswith("chimera."):
            log_name = "chimera." + log_name + f" ({log_name})"

        self.log = logging.getLogger(log_name)

        # Hz
        self._hz = 2
        self._loop_abort = threading.Event()

        # To override metadata default values
        self.__metadata_override_method__ = None

    # config implementation
    def __getitem__(self, item):
        # any thread can read if none writing at the time
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquire_read()
            return self.__config_proxy__.__getitem__(item)
        finally:
            lock.release()

    def __setitem__(self, item, value):
        # only one thread can write
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquire_write()
            return self.__config_proxy__.__setitem__(item, value)
        finally:
            lock.release()

    # bulk configuration (pass a dict to config multiple values)
    def __iadd__(self, config_dict):
        # only one thread can write
        lock = getattr(self, RWLOCK_ATTRIBUTE_NAME)
        try:
            lock.acquire_write()
            self.__config_proxy__.__iadd__(config_dict)
        finally:
            lock.release()
            return self.get_proxy()

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

    def notify_all(self):
        return getattr(self, INSTANCE_MONITOR_ATTRIBUTE_NAME).notify_all()

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

    def get_hz(self):
        return self._hz

    def set_hz(self, freq):
        tmp_hz = self.get_hz()
        self._hz = freq
        return tmp_hz

    def __main__(self):
        self._loop_abort.clear()
        run_condition = True

        while run_condition:
            t0 = time.time()
            with self:
                run_condition = self.control()

            if self._loop_abort.is_set():
                return True

            loop_time = time.time() - t0
            time_to_wake_up = (1.0 / self.get_hz()) - loop_time
            if time_to_wake_up > 0:
                # FIXME: we should use some condvar to wait until someone notify us or time_to_wake_up is over
                #        so we can release the GIL but also be alert in case someone kill this object.
                time.sleep(time_to_wake_up)
            else:
                self.log.warning(
                    f"Loop is taking more than {1.0 / self.get_hz()} seconds to run."
                )

        return True

    def __abort_loop__(self):
        self._loop_abort.set()

    def control(self):
        return False

    def get_state(self):
        return self.__state__

    def __setstate__(self, state):
        oldstate = self.__state__
        self.__state__ = state
        return oldstate

    def get_location(self):
        return self.__location__

    def __setlocation__(self, location):
        self.__location__ = Location(location)
        return True

    def get_manager(self):
        return Proxy(
            f"{self.__location__.host}:{self.__location__.port}/Manager/manager"
        )

    def get_metadata(self, request):
        # Check first if there is metadata from a metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        return []

    def set_metadata_method(self, location):
        # Defines an alternative class to get_metadata()
        self.__metadata_override_method__ = location

    def get_metadata_override(self, request):
        # Returns metadata from the override class or None if there is no override get_metadata() class.
        if self.__metadata_override_method__ is not None:
            return (
                self.get_manager()
                .get_proxy(self.__metadata_override_method__)
                .get_metadata(request)
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

    def get_proxy(self) -> Proxy:
        return Proxy(self.__location__)
