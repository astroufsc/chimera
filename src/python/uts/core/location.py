#! /usr/bin/python
# -*- coding: iso8859-1 -*-

import re
import logging

from types import (DictType, ListType,
                   TupleType, StringType)


from config import Config

class Location(object):

    def __init__(self, location):

        self._re =  re.compile('/+(?P<class>[\w]*)/+(?P<name>[\w]*)\??(?P<options>[\w\S\s=,]*)')

        self._class = "class"
        self._name = "name"
        self._options = Config()

        self._valid = True

        try:
            if type(location) == DictType:
                self._class         = location["class"]
                self._name          = location["name"]
                self._options       = Config(location["options"])
                
            elif type(location) in [ListType, TupleType]:
                self._class         = location[1]
                self._name          = location[2]
                self._options       = Config(location[3])

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

            opts = Config()

            if tmpOpts:
                for opt in tmpOpts.split(","):
                    k, v = opt.split("=")
                    opts[k.strip()] = v.strip()

        else :
            self._valid = False
            cls  = "class"
            name = "name"
            opts = Config()

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
