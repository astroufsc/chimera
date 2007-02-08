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


class InterfaceMeta(type):

    def __new__(metacls, clsname, bases, dictionary):
        
        _evs = []

        # search for event in the class
        for name, obj in dictionary.iteritems():
            if callable(obj) and not name.startswith('__') and hasattr(obj, 'event'):
                _evs.append(name)

        for name in _evs:
            del dictionary[name]

        # search for events in class bases
        for base in bases:
            if hasattr(base, '__events__'):
                _evs += base.__events__

        dictionary['__events__'] = _evs

        
        # look for configurations

        _options = {}
        
        for name, obj in dictionary.iteritems():
            if name == "__options__":
                _options.update(obj)

        # search for configs in class bases
        for base in bases:
            if hasattr(base, '__options__'):
                _options.update(base.__options__)

        dictionary['__options__'] = _options
        
        return super(InterfaceMeta, metacls).__new__(metacls, clsname, bases, dictionary)


class Interface(object):

    __metaclass__ = InterfaceMeta


if __name__ == '__main__':

    from uts.core.event import event, EventsProxy

    class IInstrument(Interface):
    
        def __init__(self, manager):
            pass
        
        def init(self):
            pass
        
        def shutdown(self):
            pass
        
        @event
        def initComplete(self):
            pass
        
        @event    
        def shutdownComplete(self):
            pass

    class ITelescopeSlew(Interface):
    
        def slew(self, coord):
            pass
        
        def abortSlew(self):
            pass
        
        def moveAxis(self, axis, offset):
            pass
        
        # events
        
        @event
        def slewComplete(self, position, tracking, trackingRate):
            pass
        
        @event
        def abortComplete(self, position):
            pass
        
        @event
        def targetChanged(self, position):
            pass
        
    class ITelescopeTracking(Interface):
        
        # methods
        def setTracking(self, track, trackingRate):
            pass
        
        # events
        @event
        def trackingRateChanged(self, trackingRate):
            pass
    

    class Instrument(IInstrument):

        def __init__(self, manager):
            self.events = EventsProxy(self.__events__)

        def __getattr__(self, attr):
            if attr in self.events:
                return self.events[attr]
            else:
                raise AttributeError

    class Telescope(Instrument, ITelescopeSlew):

        def __init__(self, manager):
            Instrument.__init__(self, manager)

    t = Telescope(None)
    print t.__events__



    

            



    
