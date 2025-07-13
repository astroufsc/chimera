# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.classloader import ClassLoader
from chimera.core.server import Server
from chimera.core.resources import ResourcesManager
from chimera.core.location import Location

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy
from chimera.core.state import State

from chimera.core.exceptions import (
    InvalidLocationException,
    ObjectNotFoundException,
    NotValidChimeraObjectException,
    ChimeraObjectException,
    ChimeraException,
    OptionConversionException,
)

from chimera.core.constants import (
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
    MANAGER_LOCATION,
)

import logging
import threading
import time


__all__ = ["Manager", "get_manager_uri", "ManagerNotFoundException"]


log = logging.getLogger(__name__)


class ManagerNotFoundException(ChimeraException):
    pass


def get_manager_uri(host=None, port=None):

    host = host or MANAGER_DEFAULT_HOST
    port = port or MANAGER_DEFAULT_PORT

    return f"{host}:{port}{MANAGER_LOCATION}"


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

    @staticmethod
    def locate(host, port=MANAGER_DEFAULT_PORT) -> Proxy:
        p = Proxy(Location(get_manager_uri(host, port)))
        if not p.ping():
            raise ManagerNotFoundException(
                f"Couldn't find manager running on {host}:{port}"
            )
        return p

    def __init__(self, host=MANAGER_DEFAULT_HOST, port=MANAGER_DEFAULT_PORT):
        log.info("Starting manager.")

        self.resources = ResourcesManager()
        self.class_loader = ClassLoader()

        # shutdown event
        self.died = threading.Event()

        # register ourselves
        self.resources.add(get_manager_uri(host, port), self),

        # our daemon server
        self.server = Server(self.resources, host, port)
        self.server.start()
        self.server_thread = threading.Thread(target=self.server.loop, daemon=True)
        self.server_thread.name = get_manager_uri(host, port)

        self.server_thread.start()

    # private
    def __repr__(self):
        return f"<Manager for {self.server.transport.host}:{self.server.transport.port} at {hex(id(self))}>"

    # host/port
    def get_hostname(self):
        return self.server.transport.host

    def get_port(self):
        return self.server.transport.port

    # reflection (console)
    def get_resources(self):
        """
        Returns a list with the Location of all the available resources
        """
        return list(self.resources.keys())

    def get_resources_by_class(self, cls):
        ret = self.resources.get_by_class(cls)
        return [x.location for x in ret]

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

        @param name: Instance name.
        @type name: str

        @param host: Manager's hostname.
        @type host: str

        @param port: Manager's port.
        @type port: int

        @raises NotValidChimeraObjectException: When a object which doesn't
                                                inherit from ChimeraObject
                                                is given in location.
        @raises ObjectNotFoundException: When te request object or the Manager
                                         was not found.
        @raises InvalidLocationException: When the requested location is invalid.

        @return: Proxy for selected object.
        @rtype: Proxy
        """

        location = Location(location)
        resolved_location = Location(
            host=location.host or self.get_hostname(),
            port=location.port or self.get_port(),
            cls=location.cls,
            name=location.name,
            config=location.config,
        )

        return Proxy(resolved_location)

    def get_instance(self, location):
        if not location:
            raise ObjectNotFoundException(
                "Couldn't find an object at the" f" given location {location}"
            )
        ret = self.resources.get(location)

        if not ret:
            raise ObjectNotFoundException(
                "Couldn't found an object at the" f" given location {location}"
            )

        return ret

    # shutdown management

    def shutdown(self):
        """
        Ask the system to shut down. Closing all sockets and stopping
        all threads.

        @return: Nothing
        @rtype: None
        """

        # die, but only if we are alive ;)
        if not self.died.is_set():

            log.info("Shutting down manager.")

            # stop objects
            try:

                elderly_first = sorted(
                    self.resources.values(), key=lambda res: res.created, reverse=True
                )

                for resource in elderly_first:

                    # except Manager
                    if resource.location == MANAGER_LOCATION:
                        continue

                    # stop object
                    self.stop(resource.location)

            except ChimeraException:
                pass
            finally:
                # kill our server
                self.server.stop()

                self.server_thread.join()

                # die!
                self.died.set()
                log.info("Manager finished.")

    def wait(self):
        """
        Ask the system to wait until anyone calls L{shutdown}.

        If nobody calls L{shutdown}, you can stop the system using
        Ctrl+C.

        @return: Nothing
        @rtype: None
        """

        try:
            try:
                while not self.died.is_set():
                    time.sleep(1)
            except IOError:
                # On Windows, Ctrl+C on a sleep call raise IOError 'cause
                # of the interrupted syscall
                pass
        except KeyboardInterrupt:
            # On Windows, Ctrl+C on a sleep call raise IOError 'cause
            # of the interrupted syscall
            self.shutdown()

    # objects lifecycle
    def add_location(self, location, path=[], start=True):
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

        if not isinstance(location, Location):
            location = Location(location)

        # get the class
        cls = None
        cls = self.class_loader.load_class(location.cls, path)
        return self.add_class(cls, location.name, location.config, start)

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

        location = Location(
            cls=cls.__name__,
            name=name,
            config=config,
            host=self.get_hostname(),
            port=self.get_port(),
        )

        # names must not start with a digit
        if location.name[0] in "0123456789":
            raise InvalidLocationException(
                f"Invalid instance name: {location} (must start with a letter)"
            )

        if location in self.resources:
            raise InvalidLocationException(
                f"Location {location} is already in the system. Only one allowed (Tip: change the name!)."
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
            log.exception(f"Error in {location} __init__.")
            raise ChimeraObjectException(f"Error in {location} __init__.")

        try:
            for k, v in list(location.config.items()):
                obj[k] = v
        except (OptionConversionException, KeyError) as e:
            log.exception(f"Error configuring {location}.")
            raise ChimeraObjectException(f"Error configuring {location}. ({e})")

        # connect
        obj.__setlocation__(location)
        self.resources.add(location, obj)

        if start:
            self.start(location)

        return Proxy(location)

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

    def start(self, location):
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

            loop = threading.Thread(target=resource.instance.__main__, daemon=True)
            loop.name = str(resource.location)
            loop.start()

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
            if resource.loop and resource.loop.is_alive():
                resource.instance.__abort_loop__()
                try:
                    resource.loop.join()
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
