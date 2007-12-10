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


import re

import logging
import chimera.core.log
log = logging.getLogger(__name__)

from types import DictType, StringType


class Location(object):
    """
    Location represents an specific resource available on the system.
    This location is the resource address onthe system.

    Location objects are immutable, so please, respect this or hash operations
    will fail.
    """

    _re = re.compile('/+(?P<class>[\w]*)/+(?P<name>[\w]*)\??(?P<config>[\w\S\s=,]*)')   

    def __init__(self, location = None, **options):

        self._class  = None
        self._name   = None
        self._config = None
        self._valid = False

        # simple string
        if isinstance(location, StringType):
            (self._class, self._name, self._config) = self.parse(location)

            if self._class and self._name and type(self._config) == DictType:
                self._valid = True

        # copy constructor
        elif isinstance(location, Location):
            self._class  = location.cls
            self._name   = location.name
            self._config = location.config
            self._valid  = location.isValid()

        # from dict
        else:
            # get from options dict (cls, name, config)
            l = "/%s/%s" % (options.get('cls', ''), options.get('name', ''))

            self._class, self._name, _ = self.parse(l)
            self._config = options.get('config', {})
            
            if self._class and self._name and type(self._config) == DictType:
                self._valid = True

    cls     = property(lambda self: self._class)
    name    = property(lambda self: self._name)
    config  = property(lambda self: self._config)
                
    def isValid(self):
        return self._valid

    def parse(self, location):

        matches = self._re.search(location)

        if not matches:
            log.warning ("Cannot parse '%s' as a valid location." % location)
            return (None, None, None)

        cls, name, tmpConfig = matches.groups()

        conf = {}

        if tmpConfig:

            for opt in tmpConfig.split(","):
                try:
                    k, v = opt.split("=")
                    conf[k.strip()] = v.strip()
                except ValueError:
                    # split returned less/more than 2 srings
                    log.warning ("Cannot parse '%s' as a valid location. "
                                 "Invalid config dict: '%s'" % (location, tmpConfig))
                    
                    return (None, None, None)
                
        return (cls, name, conf)

    def __eq__(self, loc):

        if not isinstance (loc, Location):
            loc = Location (loc)

            if not loc.isValid ():
                return False

        return (loc.cls == self.cls) and \
               (loc.name == self.name)

    def __ne__ (self, loc):
        return not self.__eq__ (loc)

    def __hash__ (self):
        return (hash(self.cls) ^ hash(self.name))

    def __repr__(self):
        _str = "/%s/%s" % (self._class, self._name)
        return _str

