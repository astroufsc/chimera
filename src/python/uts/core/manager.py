#! /usr/bin/python
#! -*- coding: iso-8859-1 -*-

from uts.core.register import Register
from uts.core.proxy import Proxy
from uts.core.location import Location

import sys
import os.path
import logging

class Manager(object):

    def __init__(self):
        logging.debug("Starting manager.")

        self._includePath = []

        self._instruments = Register()
        self._controllers = Register()

        self._pool = None

        self._cache = { }

    def appendPath(self, path):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        logging.debug("Adding %s to include path." % path)
        self._includePath.append(path)

    def setPool(self, pool):
        self._pool = pool

    def addInstrument(self, location):
        cls = self._getClass(location._class)

        if cls:
            return self._instruments.register(location, cls(self, location))
        else:
            return False
                          
    def removeInstrument(self, location):
        self._instruments.unregister(location)

    def addController(self, location):
        cls = self._getClass(location._class)

        if cls:
            return self._controllers.register(location, cls(self, location))
        else:
            return False

    def removeController(self, location):

        self._controllers.unregister(location)

    def initInstrument(self, location):

        if(not location in self._instruments):
            return False

        if(not self._pool):
            logging.debug("There is no thread pool avaiable.")
            logging.debug("You should create one and set with setPool.")
            return False

        logging.debug("Initializing instrument %s." % location)
        self._pool.queueTask(self._instruments[location].main)

    def initController(self, location):

        if(not location in self._controllers):
            return False

        if(not self._pool):
            logging.debug("There is no thread pool avaiable.")
            logging.debug("You should create one and set with setPool.")
            return False

        logging.debug("Initializing controller %s." % location)
        self._pool.queueTask(self._controllers[location].main)

    def stopInstrument(self, location):
        try:
            self._instruments[location].term.set()
            logging.debug("Stopping instrument %s." % location)
        except KeyError:
            return False

    def stopController(self, location):
        try:
            self._controllers[location].term.set()
            logging.debug("Stopping controller %s." % location)
        except KeyError:
            return False

    def stopAll(self):

        for location in self._controllers.keys():
            self.stopController(location)
            self.removeController(location)

        for location in self._instruments.keys():
            self.stopInstrument(location)
            self.removeInstrument(location)

    def getProxy(self, location):

        # FIXME: extend to controllers

        inst = self._instruments.get(Location(location))

        if inst:
            return Proxy(inst, self._pool)
        else:
            return None

    def _getClass(self, name):
        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        if name in self._cache:
            return self._cache[name]

        for path in self._includePath:
            if path not in sys.path:
                sys.path.insert(0, path)

        try:
            module = __import__(name.lower(), globals(), locals(), [name])
            logging.debug("Loading class %s from %s" % (name, module.__file__))

        except ImportError:
	    logging.exception("Couldn't load class %s.\nsys.path = %s\nException follows..." % (name, sys.path))
            return None

        self._cache[name] = vars(module)[name]

        return self._cache[name]

