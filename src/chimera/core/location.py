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

from chimera.core.exceptions import InvalidLocationException


class Location(object):
    """
    Location represents an specific resource available on the system.
    This location is the resource address onthe system.

    Location objects are immutable, so please, respect this or hash operations
    will fail.
    """

    _re = re.compile('^(?P<host>[\w.]+)?(?(host)(?P<sep>:))?(?(sep)(?P<port>[\d]+))/+(?P<class>[\w]*)/+(?P<name>[\w]*)(?P<sep2>\??)?(?(sep2)(?P<config>[\w\S\s=,]*))')

    def __init__(self, location = None, **options):

        self._host   = None
        self._port   = None
        self._class  = None
        self._name   = None
        self._config = None

        # simple string
        if isinstance(location, StringType):
            (self._host, self._port, self._class, self._name, self._config) = self.parse(location)

        # copy constructor
        elif isinstance(location, Location):
            self._host   = location.host
            self._port   = location.port
            self._class  = location.cls
            self._name   = location.name
            self._config = location.config

        # from dict
        else:
            # get from options dict (cls, name, config)
            l = "/%s/%s" % (options.get('cls', ''), options.get('name', ''))

            _, __, self._class, self._name, ___ = self.parse(l)

            self._config = options.get('config', {})
            self._host = options.get('host', None)
            self._port = options.get('port', None)

            if self._port:
                try:
                    self._port = int(self._port)
                except ValueError:
                    raise InvalidLocationException("Invalid location, port should be an "
                                                   "integer not a %s (%s)." % (type(self._port), self._port))
            
    host    = property(lambda self: self._host)
    port    = property(lambda self: self._port)
    cls     = property(lambda self: self._class)
    name    = property(lambda self: self._name)
    config  = property(lambda self: self._config)

    def parse(self, location):

        m = self._re.search(location)

        if not m:
            raise InvalidLocationException("Cannot parse '%s' as a valid location." % location)

        matches = m.groupdict()

        conf = {}

        if matches["config"]:

            for opt in matches['config'].split(","):
                try:
                    k, v = opt.split("=")
                    conf[k.strip()] = v.strip()
                except ValueError:
                    # split returned less/more than 2 srings
                    raise InvalidLocationException("Cannot parse '%s' as a valid location. "
                                                   "Invalid config dict: '%s'" % (location, matches['config']))

        port = matches['port']
        if port:
            # don't expect ValueError because RE already check this
            port = int(port)

        if not matches['name']:
            raise InvalidLocationException("Invalid location name (must be non-blank).")
        
        if not matches['class']:
            raise InvalidLocationException("Invalid location class name (must be non-blank).")

        return (matches['host'], port, matches['class'], matches['name'], conf)

    def __eq__(self, loc):

        if not isinstance (loc, Location):
            loc = Location (loc)

        return (loc.cls == self.cls)  and \
               (loc.name == self.name)

    def __ne__ (self, loc):
        return not self.__eq__ (loc)

    def __hash__ (self):
        return (hash(self.cls) ^ hash(self.name))

    def __repr__(self):

        _str = "/%s/%s" % (self._class, self._name)

        if self.host and self.port:
            _str = '%s:%d%s' % (self.host, self.port, _str)

        if self.host and not self.port:
            _str = '%s%s' % (self.host, _str)

        return _str

