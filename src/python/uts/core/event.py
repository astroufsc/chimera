#! /usr;bin/python
# -*- coding: iso-8859-1 -*-

def event(f):
    f.event = True
    return f

# based on this recipe http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410686
# by Zoran Isailovskii

# TODO: argument checking
# TODO: define delegate signature

class EventsProxy:

    def __init__(self, evs):
        self._slots = {}

        for ev in evs:
            self._slots[ev] = _EventSlot(ev)
        
    def __getitem__(self, name):
        if name in self._slots.keys():
            return self._slots[name]
        
    def __contains__(self, attr):
        return attr in self._slots.keys()
    
    def __str__(self):
        return 'Events' + str(self._slots)

    def __repr__(self):
        return self.__str__()

class _EventSlot:

    def __init__(self, name):
        self.targets = []
        self.__name__ = name
        
    def __str__(self):
        return 'event ' + self.__name__

    def __repr__(self):
        return self.__str__()

    def __call__(self, *a, **kw):
        for f in self.targets: f(*a, **kw)
    
    def __iadd__(self, f):
        self.targets.append(f)
        return self

    def __isub__(self, f):
        while f in self.targets: self.targets.remove(f)
        return self


if __name__ == '__main__':

    from uts.core.instrument import Instrument

    class ExampleDefinition(Instrument):

        def __init__(self):
            Instrument.__init__(self)

        def doSomething(self, data):
            self.somethingHappened(self, data)

        @event
        def somethingHappened(self, obj, data):
            pass

    class ExampleUsage(object):

        def __init__(self, obj):
            obj.somethingHappened += self.somethingHappened

        def somethingHappened(self, obj, data):
            print self, obj, data

    ex = ExampleDefinition()
    us = ExampleUsage(ex)

    ex.doSomething("now")
