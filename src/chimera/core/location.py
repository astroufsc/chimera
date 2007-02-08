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

import re
import logging

from types import (DictType, ListType,
                   TupleType, StringType)


class Location(object):

    def __init__(self, location):

        self._re =  re.compile('/+(?P<class>[\w]*)/+(?P<name>[\w]*)\??(?P<options>[\w\S\s=,]*)')

        self._class = "class"
        self._name = "name"
        self._options = {}

        self._valid = True

        try:
            if type(location) == DictType:
                self._class         = location["class"]
                self._name          = location["name"]
                self._options       = location["options"]
                
            elif type(location) in [ListType, TupleType]:
                self._class         = location[1]
                self._name          = location[2]
                self._options       = location[3]

            elif type(location) == StringType:

                (self._class, self._name, self._options) = matches = self.parse(location)

        except (KeyError, IndexError), e:
            self._valid = False

    cls     = property(lambda self: self._class)
    name    = property(lambda self: self._name)
    options = property(lambda self: self._options)
                
    def isValid(self):

        return self._valid

    def parse(self, location):

        matches = self._re.search(location)

        if matches:

            cls, name, tmpOpts = matches.groups()

            opts = {}

            if tmpOpts:
                for opt in tmpOpts.split(","):
                    k, v = opt.split("=")
                    opts[k.strip()] = v.strip()

        else :
            self._valid = False
            cls  = "class"
            name = "name"
            opts = {}

            logging.debug("Invalid location %s." % location)

        return (cls, name, opts)

    def __eq__(self, loc):

        return (loc._class == self._class) and \
               (loc._name == self._name)
    
    def __repr__(self):
        _str = "/%s/%s" % (self._class,
                           self._name)

        return _str

    def get(self):
        return self.__repr__(self)

if __name__ == '__main__':

    l = Location('/Sample/s?device=/dev/ttyS0,model=25.txt')
    print l.cls
    print l.name
    print l.options
