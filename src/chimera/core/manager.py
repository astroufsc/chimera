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


from chimera.core.classloader import ClassLoader
from chimera.core.resources   import ResourcesManager
from chimera.core.location    import Location

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.remoteobject  import RemoteObject
from chimera.core.proxy         import Proxy
from chimera.core.util          import getManagerURI
from chimera.core.state         import State

from chimera.core.exceptions   import InvalidLocationException, \
                                      ObjectNotFoundException,  \
                                      NotValidChimeraObjectException, \
                                      ChimeraObjectException, \
                                      ClassLoaderException, \
                                      ChimeraException


import chimera.core.log

from chimera.core.constants import MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT, MANAGER_LOCATION

try:
    import Pyro.core
    import Pyro.util
except ImportError, e:
    raise RuntimeError ("You must have Pyro version >= 3.6 installed.")

import logging
import socket
import threading
import signal
import time
import atexit
import sys
from types import StringType


__all__ = ['Manager']


log = logging.getLogger(__name__)


class ManagerAdapter (Pyro.core.Daemon):

    def __init__ (self, manager, host = None, port = None):

        Pyro.core.initServer(banner=False)
        
        Pyro.core.Daemon.__init__ (self,
                                   host=host or MANAGER_DEFAULT_HOST,
                                   port=port or MANAGER_DEFAULT_PORT,
                                   norange=0)

        self.useNameServer(None)
        self.connect (manager)

        # saved here to give objects a manager when they ask
        self.manager = manager

    def getManager (self):
        return self.manager

    def getProxyForObj(self, obj):
        return Proxy(uri=Pyro.core.PyroURI(self.hostname,
                                           obj.GUID(), prtcol=self.protocol, port=self.port))

    def connect(self, obj, name=None, index=None):

        URI = Pyro.core.PyroURI(self.hostname, obj.GUID(), prtcol=self.protocol, port=self.port)

        self.implementations[obj.GUID()] = (obj, name)            
        
        if index:
            self.implementations[index] = (obj, name)

        obj.setPyroDaemon(self)

        return URI


class Manager (RemoteObject):

    """
    This is the main class of Chimera.

    Use this class to get Proxies, add objects to the system, and so on.

    This class handles objetcs lifecicle as descrbibed in ILifecycle.

    @group Add/Remove: add*, remove
    @group Start/Stop: start, stop
    @group Proxy: getProxy
    @group Shutdown: wait, shutdown

    """
    
    def __init__(self, host = None, port = None):
        RemoteObject.__init__ (self)
        
        log.info("Starting manager.")

        self.resources = ResourcesManager ()
        self.classLoader = ClassLoader ()

        # identity
        self.setGUID(MANAGER_LOCATION)

        # our daemon server
        self.adapter = ManagerAdapter (self, host, port)
        self.adapterThread = threading.Thread(target=self.adapter.requestLoop)
        self.adapterThread.setDaemon(True)
        self.adapterThread.start()

        # register ourself
        self.resources.add(MANAGER_LOCATION, self, getManagerURI(host, port))

        # signals
        signal.signal(signal.SIGTERM, self._sighandler)
        signal.signal(signal.SIGINT, self._sighandler)
        atexit.register (self._sighandler)

        # shutdown event
        self.died = threading.Event()


    # private
    def __repr__ (self):
        if hasattr(self, 'adapter') and self.adapter:
            return "<Manager for %s:%d at %s>" % (self.adapter.hostname, self.adapter.port, hex(id(self)))
        else:
            return "<Manager at %s>" % hex(id(self))

    def _sighandler(self, sig = None, frame = None):
        self.shutdown()

    # adapter host/port
    def getHostname (self):
        if self.adapter:
            return self.adapter.hostname
        else:
            return None

    def getPort (self):
        if self.adapter:
            return self.adapter.port
        else:
            return None

    # reflection (console)
    def getResources (self):
        """
        Returns a list with the Location of all the available resources
        """
        return self.resources.keys()
        
    # helpers
    
    def getDaemon (self):
        return self.adapter

    def getProxy (self, location, name='0', host=None, port=None, lazy=False):
        """
        Get a proxy for the object pointed by location. The given location can contain index
        instead of names, e.g. '/Object/0' to get objects when you don't know their names.

        location can also be a class. getProxy will return an instance
        named 'name' at the given host/port (or on the current
        manager, if None given).

        host and port parameters determines which Manager we will
        lookup for location/instance. If None, look at this
        Manager. host/port is only used when location is a
        class, otherwise, host and port are determined by location
        itself.

        lazy parameter determines if Manager will try to locate the
        selected Manager at host/port and ask them for a valid
        object/instance. If False, Manager just return an proxy for
        the selected parameters but can't guarantee that the returned
        Proxy have an active object bounded.

        For objects managed by this own Manager, lazy is always False.

        @param location: Object location or class.
        @type location: Location or class

        @param name: Instance name.
        @type name: str

        @param host: Manager's hostname.
        @type host: str

        @param port: Manager's port.
        @type port: int

        @param lazy: Manager's laziness (check for already bound objects on host/port Manager)
        @type lazy: bool

        @raises NotValidChimeraObjectException: When a object which doesn't inherites from ChimeraObject is given in location.
        @raises ObjectNotFoundException: When te request object or the Manager was not found.
        @raises InvalidLocationException: When the requested location s invalid.

        @return: Proxy for selected object.
        @rtype: Proxy
        """

        if type(location) not in [StringType, Location]:
            if issubclass(location, ChimeraObject):
                location = Location(cls=location.__name__, name=name, host=host, port=port)
            else:
                raise NotValidChimeraObjectException ("Can't get a proxy from non ChimeraObject's descendent object (%s)." % location)

        else:
            location = Location(location)

        # who manages this location?
        if self._belongsToMe(location):

            ret = self.resources.get (location)
            if not ret:
                raise ObjectNotFoundException ("Couldn't found an object at the"
                                               " given location %s" % location)

            return Proxy (uri=ret.uri)
            
        else:

            if lazy:
                return Proxy(location)
            else:

                # contact other manager
                other = Proxy(location=MANAGER_LOCATION,
                              host=location.host or host,
                              port=location.port or port)
                
                if not other.ping():
                    raise ObjectNotFoundException ("Can't contact %s manager at %s." % (location, other.URI.address))

                proxy = other.getProxy(location)

                if not proxy:
                    raise ObjectNotFoundException ("Couldn't found an object at the"
                                                   " given location %s" % location)
                else:
                    return proxy

    def _belongsToMe (self, location):

        meHost = self.getHostname()
        meName = socket.gethostbyname(meHost)
        mePort = self.getPort()

        return (location.host == None or location.host in (meHost, meName)) and \
               (location.port == None or location.port == self.getPort())

    # shutdown management

    def shutdown(self):
        """
        Ask the system to shutdown. Closing all sockets and stopping
        all threads.

        @return: Nothing
        @rtype: None
        """

        # die, but only if we are alive ;)
        if not self.died.isSet():

            log.info("Shuting down manager.")

            # stop objects
            # damm 2.4, on 2.5 try/except/finally works
            try:
                try:

                    elderly_first = sorted(list(self.resources.values()),
                                           cmp=lambda x, y: cmp(x.created, y.created),
                                           reverse=True)

                    for resource in elderly_first:

                        # except Manager
                        if resource.location == MANAGER_LOCATION: continue

                        # stop object
                        self.stop(resource.location)
                    
                except ChimeraException:
                    pass
            finally:
                # kill our adapter
                self.adapter.shutdown(disconnect=True)

                # die!
                self.died.set()
                log.info("Manager finished.")

    def wait (self):
        """
        Ask the system to wait until anyone calls L{shutdown}.

        If nobody calls L{shutdown}, you can stop the system using
        Ctrl+C.

        @return: Nothing
        @rtype: None
        """

        try:
            while not self.died.isSet():
                time.sleep (1)
        except IOError:
            # On Windows, Ctrl+C on a sleep call raise IOError 'cause
            # of the interrupted syscall
            pass


    # objects lifecycle

    def addLocation (self, location, path = [], start = True):
        """
        Add the class pointed by 'location' to the system configuring it using 'config'.

        Manager will look for the class in 'path' plus sys.path.

        @param path: The class search path.
        @type path: list

        @param start: start the object after initialization.
        @type start: bool

        @raises ChimeraObjectException: Internal error on managed (user) object.
        @raises ClassLoaderException: Class not found.
        @raises NotValidChimeraObjectException: When a object which doesn't inherites from ChimeraObject is given in location.
        @raises InvalidLocationException: When the requested location s invalid.              

        @return: retuns a proxy for the object if sucessuful, False otherwise.
        @rtype: Proxy or bool
        """

        if type(location) != Location:
            location = Location(location)

        # get the class
        cls = None

        cls = self.classLoader.loadClass(location.cls, path)
            
        return self.addClass (cls, location.name, location.config, start)


    def addClass (self, cls, name, config = {}, start = True):
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
        @raises NotValidChimeraObjectException: When a object which doesn't inherites from ChimeraObject is given in location.
        @raises InvalidLocationException: When the requested location s invalid.              

        @return: retuns a proxy for the object if sucessuful, False otherwise.
        @rtype: Proxy or bool
        """

        location = Location(cls=cls.__name__, name=name, config=config)

        # names must not start with a digit
        if location.name[0] in "0123456789":
            raise InvalidLocationException ("Invalid instance name: %s (must start with a letter)" % location)

        if location in self.resources:
            raise InvalidLocationException ("Location %s is already in the system. Only one allowed (Tip. change the name!)." % location)

        # check if it's a valid ChimeraObject
        if not issubclass(cls, ChimeraObject):
            raise NotValidChimeraObjectException ("Cannot add the class %s. It doesn't descend from ChimeraObject." % cls.__name__)
        
        # run object __init__ and configure using location configuration
        # it runs on the same thread, so be a good boy
        # and don't block manager's thread
        try:
            obj = cls()
            for k, v in location.config.items():
                obj[k] = v
        except Exception:
            log.exception("Error in %s __init__." % location)
            raise ChimeraObjectException("Error in %s __init__." % location)

        # connect
        obj.__setlocation__(location)
        next = len(self.resources.getByClass(location.cls))
        uri  = self.adapter.connect(obj, index=str(Location(cls=location.cls, name=next)))
        self.resources.add(location, obj, uri)
        
        if start:
            self.start(location)
                
        return Proxy(uri=uri)
       

    def remove (self, location):
        """
        Remove the object pointed by 'location' from the system
        stopping it before if needed.

        @param location: The object to remove.
        @type location: Location,str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException ("Location %s was not found." % location)

        self.stop(location)

        resource = self.resources.get(location)
        self.adapter.disconnect (resource.instance)
        self.resources.remove (location)        

        return True
      

    def start (self, location):
        """
        Start the object pointed by 'location'.

        @param location: The object to start.
        @type location: Location or str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.
        
        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException ("Location %s was not found." % location)
            
        log.info("Starting %s." % location)            

        resource = self.resources.get(location)

        if resource.instance.getState() == State.RUNNING:
            return True

        try:
            resource.instance.__start__()
            
        except Exception:
            log.exception ("Error running %s __start__ method." % location)
            raise ChimeraObjectException("Error running %s __start__ method." % location)

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            log.info("Running %s. __main___." % location)                        

            loop = threading.Thread(target=resource.instance.__main__)
            loop.setDaemon(True)
            loop.start()

            resource.instance.__setstate__(State.RUNNING)
            resource.created = time.time()
            resource.loop = loop

            return True

        except Exception, e:
            log.exception("Error running %s __main__ method." % location)
            resource.instance.__setstate__(State.STOPPED)
            raise ChimeraObjectException("Error running %s __main__ method." % location)


    def stop (self, location):
        """
        Stop the object pointed by 'location'.

        @param location: The object to stop.
        @type location: Location or str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """
    
        if location not in self.resources:
            raise ObjectNotFoundException ("Location %s was not found." % location)

        log.info("Stopping %s." % location)
            
        resource = self.resources.get(location)

        try:

            # stop control loop
            if resource.loop and resource.loop.isAlive():
                resource.instance.__abort_loop__()
                resource.loop.join()

            if resource.instance.getState() != State.STOPPED:
                resource.instance.__stop__ ()

            return True

        except Exception, e:
            log.exception("Error running %s __stop__ method. Exception follows..." % location)
            raise ChimeraObjectException("Error running %s __stop__ method." % location)

