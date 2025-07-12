# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import concurrent.futures
import logging
import operator
import threading
import time
from collections.abc import Callable
from typing import Any, Literal

from chimera.core.bus import Bus
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.classloader import ClassLoader
from chimera.core.constants import (
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
    MANAGER_LOCATION,
)
from chimera.core.exceptions import (
    ChimeraException,
    ChimeraObjectException,
    NotValidChimeraObjectException,
    ObjectNotFoundException,
    OptionConversionException,
)
from chimera.core.proxy import Proxy
from chimera.core.resources import ResourcesManager
from chimera.core.state import State
from chimera.core.url import parse_url

__all__ = ["Manager", "get_manager_uri", "ManagerNotFoundException"]


log = logging.getLogger(__name__)


class ManagerNotFoundException(ChimeraException):
    pass


def get_manager_uri(host: str | None = None, port: int | None = None):
    host = host or MANAGER_DEFAULT_HOST
    port = port or MANAGER_DEFAULT_PORT

    return parse_url(f"{host}:{port}{MANAGER_LOCATION}")


class Manager:
    """
    This is the main class of Chimera.
    Use this class to get Proxies, add objects to the system, and so on.
    This class handles objects life-cycle as described in ILifecycle.

    @group Add/Remove: add*, remove
    @group Start/Stop: start, stop
    @group Proxy: get_proxy
    @group Shutdown: wait, shutdown
    """

    def __init__(self, bus: Bus):
        log.info("Starting manager.")

        self._bus = bus
        self._bus.resolve_request = self._resolve_request

        self.resources = ResourcesManager()
        self.class_loader = ClassLoader()
        self._pool = concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=f"{self._bus.url.url}/Manager-"
        )

        # shutdown event
        self.died = threading.Event()

        # register ourselves
        self.resources.add("/Manager/manager", self)

    def _resolve_request(
        self, object: str, method: str
    ) -> tuple[bool, Literal[False] | Callable[..., Any]]:

        resource = self.resources.get(object)
        if not resource:
            return False, False
            # TODO: handle invalid request
            # self.transport.send(Protocol.error("Invalid request"))

        instance = resource.instance
        method_getter = operator.attrgetter(method)

        try:
            callable = method_getter(instance)
            return True, callable
        except AttributeError:
            return True, False

    # private
    def __repr__(self):
        return f"<Manager for {self._bus.url} at {hex(id(self))}>"

    # host/port
    def get_hostname(self):
        return self._bus.url.url.replace("tcp://", "").split(":")[0]

    def get_port(self):
        return self._bus.url.url.replace("tcp://", "").split(":")[1]

    # reflection (console)
    def get_resources(self):
        """
        Returns a list with the Location of all the available resources
        """
        return list(self.resources.keys())

    def get_resources_by_class(self, cls):
        return [r.path for r in self.resources.get_by_class(cls)]

    # helpers
    def get_proxy(self, location):
        """
        Get a proxy for the object pointed by location. The given location
        can contain index instead of names, e.g. '/Object/0' to get objects
        when you don't know their names.

        location can also be a class. get_proxy will return an instance
        named 'name' at the given host/port (or on the current
        manager, if None given).

        host and port parameters determines which Manager we will
        lookup for location/instance. If None, look at this
        Manager. host/port is only used when location is a
        class, otherwise, host and port are determined by location
        itself.

        @param location: Object location or class.
        @type location: Location or class

        @raises NotValidChimeraObjectException: When a object which doesn't
                                                inherit from ChimeraObject
                                                is given in location.
        @raises ObjectNotFoundException: When te request object or the Manager
                                         was not found.
        @raises InvalidLocationException: When the requested location is invalid.

        @return: Proxy for selected object.
        @rtype: Proxy
        """

        url = parse_url(location)
        return Proxy(url, self._bus)

    def shutdown(self):
        """
        Ask the system to shut down. Closing all sockets and stopping
        all threads.

        @return: Nothing
        @rtype: None
        """

        # die, but only if we are alive ;)
        if self.died.is_set():
            return

        log.info("Shutting down manager.")

        # stop objects
        elderly_first = sorted(
            self.resources.values(), key=lambda res: res.created, reverse=True
        )

        for resource in elderly_first:
            # except Manager
            if resource.path == MANAGER_LOCATION:
                continue

            # stop object
            try:
                self.stop(resource.path)
            except ChimeraException:
                pass

        # die!
        self.died.set()
        log.info("Manager shut down.")

    # objects lifecycle
    def add_location(self, location, path=[], start=True, config: dict[str, Any] = {}):
        """
        Add the class pointed by 'location' to the system configuring it
        using 'config'. Manager will look for the class in 'path' and sys.path.

        @param path: The class search path.
        @type path: list

        @param start: start the object after initialization.
        @type start: bool

        @raises ChimeraObjectException: Internal error on managed (user) object.
        @raises ClassLoaderException: Class not found.
        @raises NotValidChimeraObjectException: When an object which doesn't
                                                inherit from ChimeraObject is
                                                given in location.
        @raises InvalidLocationException: When the requested location s invalid.

        @return: returns a proxy for the object if successful, False otherwise.
        @rtype: Proxy or bool
        """
        # get the class
        cls = self.class_loader.load_class(location.cls, path)
        return self.add_class(cls, location.name, config, start)

    def add_class(self, cls, name, config={}, start=True):
        """
        Add the class 'cls' to the system configuring it using 'config'.

        @param cls: The class to add to the system.
        @type cls: ChimeraObject

        @param name: The name of the new class instance.
        @type name: str

        @param config: The configuration dictionary for the object.
        @type config: dict

        @param start: start the object after initialization.
        @type start: bool

        @raises ChimeraObjectException: Internal error on managed (user) object.
        @raises NotValidChimeraObjectException: When an object which doesn't inherit from ChimeraObject is given in location.
        @raises InvalidLocationException: When the requested location s invalid.

        @return: returns a proxy for the object if successful, False otherwise.
        @rtype: Proxy or bool
        """

        url = parse_url(
            f"{self.get_hostname()}:{self.get_port()}/{cls.__name__}/{name}"
        )
        # names must not start with a digit
        if url.name[0] in "0123456789":
            raise ValueError(
                f"Invalid instance name: {url.name} (must start with a letter)"
            )

        if url.path in self.resources:
            raise ValueError(
                f"Location {url.path} is already in the system. Only one allowed (Tip: change the name!)."
            )

        # check if it's a valid ChimeraObject
        if not issubclass(cls, ChimeraObject):
            raise NotValidChimeraObjectException(
                f"Cannot add the class {cls.__name__}. It doesn't descend from ChimeraObject."
            )

        # run object __init__ and configure using location configuration
        # it runs on the same thread, so be a good boy
        # and don't block manager's thread
        try:
            obj = cls()
        except Exception:
            log.exception(f"Error in {url} __init__.")
            raise ChimeraObjectException(f"Error in {url} __init__.")

        try:
            for k, v in list(config.items()):
                obj[k] = v
        except (OptionConversionException, KeyError) as e:
            log.exception(f"Error configuring {url.path}.")
            raise ChimeraObjectException(f"Error configuring {url}. ({e})")

        # connect
        obj.__location__ = str(url)
        obj.__bus__ = self._bus
        self.resources.add(url.path, obj)

        if start:
            self.start(url.path)

        return Proxy(str(url), self._bus)

    def remove(self, location):
        """
        Remove the object pointed by 'location' from the system
        stopping it before if needed.

        @param location: The object to remove.
        @type location: Location,str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.

        @return: returns True if successful. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException(f"Location {location} was not found.")

        self.stop(location)

        self.resources.get(location)
        # self.adapter.disconnect(resource.instance)
        self.resources.remove(location)

        return True

    def start(self, location) -> bool:
        """
        Start the object pointed by 'location'.

        @param location: The object to start.
        @type location: Location or str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.

        @return: returns True if successful. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException(f"Location {location} was not found.")

        log.info(f"Starting {location}.")

        resource = self.resources.get(location)

        if resource.instance.get_state() == State.RUNNING:
            return True

        try:
            resource.instance.__start__()
        except Exception:
            log.exception(f"Error running {location} __start__ method.")
            raise ChimeraObjectException(f"Error running {location} __start__ method.")

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            log.info(f"Running {location}.__main___.")

            loop = self._pool.submit(resource.instance.__main__)

            resource.instance.__setstate__(State.RUNNING)
            resource.created = time.time()
            resource.loop = loop

            return True

        except Exception:
            log.exception(f"Error running {location} __main__ method.")
            resource.instance.__setstate__(State.STOPPED)
            raise ChimeraObjectException(f"Error running {location} __main__ method.")

    def stop(self, location):
        """
        Stop the object pointed by 'location'.

        @param location: The object to stop.
        @type location: Location or str

        @raises ObjectNotFoundException: When the requested object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.

        @return: returns True if successful. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException(f"Location {location} was not found.")

        log.info(f"Stopping {location}.")

        resource = self.resources.get(location)

        try:
            # stop control loop
            if resource.loop:
                resource.instance.__abort_loop__()
                try:
                    resource.loop.cancel()
                except KeyboardInterrupt:
                    # ignore Ctrl+C on shutdown
                    pass

            if resource.instance.get_state() != State.STOPPED:
                resource.instance.__stop__()
                resource.instance.__setstate__(State.STOPPED)

            return True

        except Exception:
            log.exception(
                f"Error running {location} __stop__ method. Exception follows..."
            )
            raise ChimeraObjectException(f"Error running {location} __stop__ method.")
