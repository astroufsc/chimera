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

import sys
import os.path
import traceback
import logging
from types import StringType

from chimera.core.register import Register
from chimera.core.proxy import Proxy
from chimera.core.location import Location
from chimera.core.threads import getThreadPool

class Manager(object):

    def __init__(self, pool = None, add_system_path = True):
        logging.debug("Starting manager.")

        self._includePath = {"instrument": [],
                             "controller": [],
                             "driver"    : []}

        self._instruments = Register("instrument")
        self._controllers = Register("controller")
        self._drivers     = Register("driver")

        self._pool = pool or getThreadPool ()

        self._cache = { }

        if add_system_path:
            self._addSystemPath ()

    def shutdown(self):

        for location in self._controllers.keys():
            self.shutdownController(location)
            self.removeController(location)

        for location in self._instruments.keys():
            self.shutdownInstrument(location)
            self.removeInstrument(location)

        for location in self._drivers.keys():
            self.shutdownDriver(location)
            self.removeDriver(location)

    def _addSystemPath (self):
        
        prefix = os.path.realpath(os.path.join(os.path.abspath(__file__),
                                               '../../'))
        
        self.appendPath ("instrument", os.path.join(prefix, 'instruments'))
        self.appendPath ("controller", os.path.join(prefix, 'controllers'))
        self.appendPath ("driver", os.path.join(prefix, 'drivers'))

    def appendPath(self, kind, path):

        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        logging.debug("Adding %s to %s include path." % (path, kind))

        self._includePath[kind].append(path)

    def setPool(self, pool):
        self._pool = pool

    def _getClass(self, name, kind):
        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        # TODO: - add a reload method

        if name in self._cache:
            return self._cache[name]

        try:
            logging.debug("Looking for module %s." % name.lower())

            # adjust sys.path accordingly to kind
            tmpSysPath = sys.path
            sys.path = self._includePath[kind] + sys.path
            
            module = __import__(name.lower(), globals(), locals(), [name])

            # turns sys.path back
            sys.path = tmpSysPath

            if not name in vars(module).keys():
                logging.error("Module found but there are no class named %s on module %s (%s)." %
                              (name, name.lower(), module.__file__))
                return False

            self._cache[name] = vars(module)[name]

            logging.debug("Module %s found (%s)" % (name.lower(),
                                                    module.__file__))

            return self._cache[name]

        except Exception, e:

            # Python trick: An ImportError exception catched here
            # could came from both the __import__ above or from the
            # module imported by the __import__ above... So, we need a
            # way to know the difference between those exceptions.  A
            # simple (reliable?) way is to use the lenght of the
            # exception traceback as a indicator If the traceback had
            # only 1 entry, the exceptions comes from the __import__
            # above, more than one the exception comes from the
            # imported module

            tb_size = len(traceback.extract_tb(sys.exc_info()[2]))

            if tb_size == 1:

                if type (e) == ImportError:
                    logging.error("Couldn't found module %s." % name)

                else:
                    logging.error("Module %s found but couldn't be loaded. Exception follows..." % name)
                    logging.exception("")
                    
            else:
                logging.error("Module %s found but couldn't be loaded. Exception follows..." % name)
                logging.exception("")

            return False

    
    def _get(self, location, register, proxy = True):

        if type(location) == StringType:
            location = Location(location)

        obj = register.get(location)

        if not obj:
            # not found on register, try to add
            if not self._init (location, register):
                obj = None
            else:
                obj = register.get(location)

        if obj != None:
            if proxy:
                return Proxy(obj, self._pool)
            else:
                return obj
        else:
            return None

    def _add(self, location, register):

        # get the class
        cls = self._getClass(location._class, register.kind)

        if not cls:
            return False

        # run object constructor
        # it runs on the same thread, so be a good boy
        # and don't block manager's thread
        try:
            obj = cls(self)
            return register.register(location, obj)
                        
        except Exception:
            logging.exception("Error in %s %s constructor. Exception follows..." %
                              (register.kind, location))
            return False
    
    def _remove(self, location, register):
        return register.unregister(location)

    def _init(self, location, register):

        if(not self._pool):
            logging.debug("There is no thread pool avaiable.")
            logging.debug("You should create one and set with setPool.")
            return False

        if location not in register:
            if not self._add(location, register):
                return False

        logging.debug("Initializing %s %s." % (register.kind, location))

        # run object init
        # it runs on the same thread, so be a good boy and don't block manager's thread
        try:
            ret = register[location].init(location.options)
            if not ret:
                logging.warning ("%s init returned an error. Removing %s from register." % (location, location))
                return False
        except Exception:
            logging.exception("Error running %s %s init method. Exception follows..." %
                              (register.kind, location))
            return False

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            self._pool.queueTask(register[location].main)
        except Exception:
            logging.exception("Error running %s %s main method. Exception follows..." %
                              (register.kind, location))
            return False

        return True

    def _shutdown(self, location, register):

        if location not in register:
            return False

        try:
            logging.debug("Shutting down %s %s." % (register, location))

            # run object shutdown method
            # again: runs on the same thread, so don't block it
            register[location].shutdown()
            self._remove(location, register)
            return True

        except Exception:
            logging.exception("Error running %s %s shutdown method. Exception follows..." %
                              (register.kind, location))
            return False

    # helpers

    def getLocation(self, obj):
        # FIXME: buggy by definition
        kinds = [self._controllers, self._instruments, self._drivers]

        def _get (kind):
            return kind.getLocation (obj)

        ret = map(_get, kinds)

        for item in ret:
            if item != None:
                return item

        return None
            

    # instruments

    def getInstrument(self, location, proxy = True):
        return self._get(location, self._instruments, proxy)
    
    def addInstrument(self, location):
        return self._add(location, self._instruments)

    def removeInstrument(self, location):
        return self._remove(location, self._instruments)

    def initInstrument(self, location):
        return self._init(location, self._instruments)

    def shutdownInstrument(self, location):
        return self._shutdown(location, self._instruments)

    # controllers
    
    def getController(self, location, proxy = True):
        return self._get(location, self._controllers, proxy)

    def addController(self, location):
        return self._add(location, self._controllers)

    def removeController(self, location):
        return self._remove(location, self._controllers)

    def initController(self, location):
        return self._init(location, self._controllers)

    def shutdownController(self, location):
        return self._shutdown(location, self._controllers)

    # drivers

    def getDriver(self, location, proxy = True):
        return self._get(location, self._drivers, proxy)

    def addDriver(self, location):
        return self._add(location, self._drivers)

    def removeDriver(self, location):
        return self._remove(location, self._drivers)

    def initDriver(self, location):
        return self._init(location, self._drivers)

    def shutdownDriver(self, location):
        return self._shutdown(location, self._drivers)
