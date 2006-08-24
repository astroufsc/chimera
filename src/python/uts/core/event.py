#! /usr;bin/python
# -*- coding: iso-8859-1 -*-

def event(f):
    f.event = True
    return f

# based on this recipe http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/410686
# by Zoran Isailovskii

class EventsProxy:

    def __init__(self, evs):
        self.__events__ = evs
        
    def __getattr__(self, name):
        if hasattr(self, '__events__'):
            assert name in self.__events__, "Event '%s' is not declared" % name
        self.__dict__[name] = ev = _EventSlot(name)
        return ev
        
    def __repr__(self):
        return 'Events' + str(list(self))
    
    def __str__(self):
        return self.__repr__()

    def __contains__(self, attr):
        return attr in self.__events__

class _EventSlot:

    def __init__(self, name):
        self.targets = []
        self.__name__ = name

#   def __repr__(self):
#       return 'event ' + self.__name__

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
