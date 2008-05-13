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


from chimera.core.location   import Location
from chimera.core.exceptions import InvalidLocationException, \
                                    ObjectNotFoundException, \
                                    ChimeraException

import time
import sys


class Resource (object):

    def __init__ (self):
        self._location = None
        self._instance = None        
        self._created  = time.time ()
        self._loop     = None
        self._uri      = None        

    location = property (lambda self: self._location, lambda self, value: setattr (self, '_location', value))
    instance = property (lambda self: self._instance, lambda self, value: setattr (self, '_instance', value))    
    created  = property (lambda self: self._created, lambda self, value: setattr (self, '_created', value))
    loop     = property (lambda self: self._loop, lambda self, value: setattr (self, '_loop', value))    
    uri      = property (lambda self: self._uri,      lambda self, value: setattr (self, '_uri', value))
    
    def __str__ (self):
        return "<%s (%s) at %s>" % (self.location, self.instance, self.uri)


class ResourcesManager (object):
    
    def __init__ (self):
        self._res = {}
    
    def add (self, location, instance, uri, loop=None):

        location = self._validLocation (location)

        if location in self:
            raise InvalidLocationException("Location already on the resource pool.")

        entry = Resource ()
        entry.location = location
        entry.instance = instance
        entry.loop     = loop
        entry.uri = uri

        self._res[location] = entry

        # get the number of instances of this class (counting this one) (minus 1 to start couting at 0)
        return len(self.getByClass(location.cls)) - 1

    def remove (self, location):
        entry = self.get(location)
        del self._res[entry.location]
        return True


    def get (self, item):

        location = self._validLocation(item)

        try:
            index = int(location.name)
            return self._getByIndex(location, index)
        except ValueError:
            # not a numbered instance
            pass

        return self._get (location)

    def getByClass(self, cls):
        
        entries = filter(lambda location: location.cls == cls, self.keys())

        ret = []
        for entry in entries:
            ret.append (self.get (entry))

        ret.sort (key=lambda entry: entry.created)

        return ret

 
    def _get (self, item):

        location = self._validLocation (item)

        if location in self:
            ret = filter(lambda x: x == location, self.keys())
            return self._res[ret[0]]
        else:
            raise ObjectNotFoundException("Couldn't found %s." % location)


    def _getByIndex(self, item, index):

        location = self._validLocation (item)

        insts = self.getByClass(location.cls)

        if insts:
            try:
                return self._res[insts[index].location]
            except IndexError:
                raise ObjectNotFoundException("Couldn't found %s instance #%d." % (location, index))
        else:
            raise ObjectNotFoundException("Couldn't found %s." % location)


    def _validLocation (self, item):
       
        ret = item

        if not isinstance (item, Location):
            ret = Location (item)

        return ret

    def __getitem__(self, item):

        try:
            return self.get(item)
        except ChimeraException:
            raise KeyError("Couldn't found %s" % item), None, sys.exc_info()[2]

    def __contains__ (self, item):

        # note that our 'in'/'not in' tests are for keys (locations) and
        # not for values

        item = self._validLocation (item)

        if item in self.keys():
            return True
        else:
            # is this a numbered instance?
            try:
                index = int(item.name)
                return bool(self._getByIndex(item, index))
            except ValueError:
                # not a numbered instance
                return False
            except ObjectNotFoundException:
                # nor a valid object
                return False


    __iter__     = lambda self: self._res.__iter__ ()
    __len__      = lambda self: self._res.__len__ ()

    keys      = lambda self: self._res.keys ()
    values    = lambda self: self._res.values ()
    items     = lambda self: self._res.items ()
    iterkeys  = lambda self: self._res.iterkeys ()
    iteritems = lambda self: self._res.iteritems ()

