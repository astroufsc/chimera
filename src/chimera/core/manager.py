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


from chimera.core.classloader import ClassLoader, ClassLoaderException
from chimera.core.resources   import ResourcesManager
from chimera.core.threads     import ThreadPool
from chimera.core.location    import Location

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.remoteobject  import RemoteObject
from chimera.core.proxy         import Proxy
from chimera.core.util          import getManagerURI
from chimera.core.state         import State


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



__all__ = ['Manager']


log = logging.getLogger(__name__)


class ManagerServer (Pyro.core.Daemon):

    def __init__ (self, manager, host = None, port = None):

        Pyro.core.initServer(banner=False)
        
        Pyro.core.Daemon.__init__ (self,
                                   host=host or MANAGER_DEFAULT_HOST,
                                   port=port or MANAGER_DEFAULT_PORT)

        self.useNameServer(None)
        self.connect (manager)

        # saved here to give objects a manager when they ask
        self.manager = manager

    def getManager (self):
        return self.manager

    def getProxyForObj(self, obj):
        return Proxy(uri=Pyro.core.PyroURI(self.hostname,
                                           obj.GUID(), prtcol=self.protocol, port=self.port))

    def connect(self, object, name=None, index=None):

        URI = Pyro.core.PyroURI(self.hostname, object.GUID(), prtcol=self.protocol, port=self.port)

        # enter the (object,name) in the known implementations dictionary
        if index:
            self.implementations[index]=(object,name)
        else:
            self.implementations[object.GUID()]=(object,name)            
        
        object.setPyroDaemon(self)
        return URI


class Manager (RemoteObject):

    """
    This is the main class of Chimera.

    Use this class to get Proxies, add objects to the system, and so on.

    This class handles objetcs lifecicle as descrbibed in L{ILifecycle}.

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
        self.pool = ThreadPool ()

        # identity
        self.setGUID(MANAGER_LOCATION)

        # our daemon server
        self.daemon = ManagerServer (self, host, port)
        self.pool.queueTask (self.daemon.requestLoop)

        # register ourself
        self.resources.add(MANAGER_LOCATION, self, getManagerURI())

        # signals
        signal.signal(signal.SIGTERM, self._sighandler)
        signal.signal(signal.SIGINT, self._sighandler)
        atexit.register (self._sighandler)

        # shutdown event
        self.died = threading.Event()


    # private
    def __repr__ (self):
        return "<Manager for '%s:%d' at %s>" % (self.daemon.hostname, self.daemon.port, hex(id(self)))

    def _sighandler(self, sig = None, frame = None):
        self.shutdown()

    
    # helpers
    
    def getDaemon (self):
        return self.daemon

    def getPool (self):
        return self.pool

    def getProxy (self, location):
        """
        Get a proxy for the object pointed by 'location'. The given location can contain index
        instead of names, e.g. '/Object/0' to get objects when you don't know their names.

        @param location: Object location.
        @type location: Location or str

        @return: Proxy for 'location'
        @rtype: Proxy
        """

        ret = self.resources.get (location)

        if not ret:
            return False

        return Proxy (uri=ret.uri)


    # shutdown management

    def shutdown(self):
        """
        Ask the system to shutdown. Closing all sockets and stopping all threads.

        @return: Nothing
        @rtype: None
        """

        # die, but only if we are alive ;)
        if not self.died.isSet():

            log.info("Shuting down manager.")

            # stop objects
            for location in self.resources:
                # except ourself
                if location == MANAGER_LOCATION: continue
                
                self.stop(location)

            self.daemon.shutdown(disconnect=True)
            del self.daemon
        
            self.pool.joinAll()
            self.died.set()
        
            log.info("Manager finished.")

    def wait (self):
        """
        Ask the system to wait until anyone calls L{shutdown}.

        If nobody calls L{shutdown}, you can stop the system using Ctrl+C.

        @return: Nothing
        @rtype: None
        """

        while not self.died.isSet():
            time.sleep (1)


    # objects lifecycle

    def addLocation (self, location, config = {}, path = [], start = True):
        """
        Add the class pointed by 'location' to the system configuring it using 'config'.

        Manager will look for the class in 'path' plus sys.path.

        @param location: The object location.
        @type location: Location or str

        @param config: The configuration dictionary for the object.
        @type config: dict

        @param path: The class search path.
        @type path: list

        @param start: start the object after initialization.
        @type start: bool

        @return: retuns a proxy for the object if sucessuful, False otherwise.
        @rtype: Proxy or bool
        """

        if type(location) != Location:
            location = Location(location)

        if not location.isValid():
            log.warning ("Invalid location: %s" % location)
            return False

        # get the class
        cls = None
        
        try:
            cls = self.classLoader.loadClass(location.cls, path)
        except ClassLoaderException, e:
            log.warning ("Error while looking for '%s' class." % location.cls)
            log.exception (e)
            return False
            
        return self.addClass (cls, location.name, config, start)


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

        @return: retuns a proxy for the object if sucessuful, False otherwise.
        @rtype: Proxy or bool
        """

        location = Location(cls = cls.__name__, name = name)

        if not location.isValid():
            log.warning ("Invalid location: %s" % location)
            return False

        if location in self.resources:
            log.warning ("Location '%s' already in the system. Only one allowed (Tip. change the name!)." % location)
            return False

        # check if it's a valid ChimeraObject
        if not issubclass(cls, ChimeraObject):
            log.warning("Cannot add the class '%s'. It doesn't descend from ChimeraObject." % cls.__name__)
            return False
        
        # run object __init__
        # it runs on the same thread, so be a good boy
        # and don't block manager's thread
        try:
            obj = cls()
        except Exception, e:
            log.warning("Error in %s __init__." % location)
            log.exception(e)            
            return False

        # connect with URI
        obj.__setlocation__(location)
        uri = self.daemon.connect(obj)
        index = self.resources.add(location, obj, uri)
        
        # connect with index (to handle numbered locations)
        self.daemon.connect(obj, index=str(Location((location.cls, index, location.config))))
        
        if start:
            if not self.start (location):
                return False
                
        return Proxy(uri=uri)
       

    def remove (self, location):
        """
        Remove the object pointed by 'location' from the system.

        @param location: The object to remove.
        @type: Location or str

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            log.warning ("Location not available: %s." % location)
            return False

        if not self.stop (location):
            log.warning ("Couldn't stop resource %s." % location)
            return False

        resource = self.resources.get(location)
        self.daemon.disconnect (resource.instance)
        self.resources.remove (location)        

        return True
      

    def start (self, location):
        """
        Start the object pointed by 'location'.

        @param location: The object to start.
        @type: Location or str

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            log.warning ("Location '%s' was not found." % location)
            return False
            
        log.info("Starting %s." % location)            

        resource = self.resources.get(location)

        if resource.instance.getState() == State.RUNNING:
            return True

        try:
            ret = resource.instance.__start__()
            if not ret:
                log.warning ("%s __start__ returned an error. Removing %s from register." % (location, location))
                return False
            
        except Exception, e:
            log.warning ("Error running %s __start__ method. Exception follows..." % location)
            log.exception(e)
            return False

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            log.info("Running %s. __main___." % location)                        

            self.pool.queueTask(resource.instance.__main__)

            resource.instance.__setstate__(State.RUNNING)            

            return True

        except Exception, e:
            log.info("Error running %s __main__ method. Exception follows..." % location)
            log.exception (e)
            
            resource.instance.__setstate__(State.STOPPED)
            
            return False


    def stop (self, location):
        """
        Stop the object pointed by 'location'.

        @param location: The object to stop.
        @type: Location or str

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """
    
        if location not in self.resources:
            log.warning ("Location not available: %s." % location)
            return False

        log.info("Stopping %s." % location)
            
        resource = self.resources.get(location)

        try:

            if resource.instance.getState() != State.STOPPED:
                resource.instance.__stop__ ()

            return True

        except Exception, e:
            log.info("Error running %s __stop__ method. Exception follows..." % location)
            log.exception (e)
            return False

