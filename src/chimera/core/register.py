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

from chimera.core.location import Location

class Register(object):

    def __init__(self, kind = None):

        self.objects = {}
        self.kind = kind or "object"

    def register(self, location, instance):

        if location in self.objects:
            return False

        self.objects[location] = instance
        return True

    def unregister(self, location):
        if not location in self.objects:
            return False

        del self.objects[location]
        return True

    def update(self, location, instance):
        return self.unregister(location) and self.register(location, instance)

    def __repr__(self):
        _str = "There are %d %s(s) avaiable.\n" % (len(self.objects), self.kind)
        _str += self.objects.__repr__()
        
        return _str

    def __contains__(self, item):

        if not isinstance (item, Location):
            item = Location (item)

        if not item.isValid():
            return None

        _ret = filter(lambda x: x == item, self.objects.keys())

        if _ret:
            return True
        else:
            return False

    def __len__(self):
        return self.objects.__len__()

    def __iter__(self):
        return self.objects.__iter__()

    def items(self):
        return self.objects.items()

    def keys(self):
        return self.objects.keys()

    def values(self):
        return self.objects.values()
    
    def __getitem__(self, item):

        r = self.get(item)

        if not r:
            raise KeyError
        else:
            return r

    def get(self, item):

        if not isinstance (item, Location):
            item = Location (item)

        if not item.isValid():
            return None

        try:
            number = int(item._name)
            return self.getByIndex(item._class, number)
        except ValueError:
            # not a numbered instance
            pass

        if self.__contains__(item):
            ret = filter(lambda x: x == item, self.objects.keys())
            return self.objects[ret[0]]
        else:
            return None

    def getByClass(self, cls):

        _insts = filter(lambda inst: inst._class == cls, self.objects.keys())

        return _insts

    def getByIndex(self, cls, index):
        
        insts = self.getByClass(cls)

        if insts:
            try:
                return self[insts.pop(index)]
            except IndexError:
                return False
        else:
            return False

    def getLocation(self, instance):
        
        if not instance in self.objects.values():
            return None

        for location, inst in self.objects.items():
            if inst == instance:
                return location

if __name__ == '__main__':

    from chimera.core.location import Location
    a = object()
    l = Location("/Telescope/meade?opt1=val1,opt2=val2")

    b = object()
    ll = Location("/Telescope/paramount?opt1=val1,opt2=val2")


    reg = Register()
    reg.register(l, a)
    reg.register(ll, b)

    print reg
    print reg[l]
    print reg["/Telescope/meade"]

    lll = reg.getByClass("Telescope")
    for i in lll:
        print reg[i]
