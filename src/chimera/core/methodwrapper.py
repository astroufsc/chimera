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

import logging

import chimera.core.log
log = logging.getLogger(__name__)


__all__ = ['MethodWrapper',
           'MethodWrapperDispatcher']


class MethodWrapper (object):

    __name__ = ""
    
    def __init__ (self, func, specials = None, dispatcher = None):

        # our wrapped function
        self.func = func

        # will be bounded by the descriptor get
        self.cls = None        
        self.instance = None
        
        self.specials   = specials or {}
        self.dispatcher = dispatcher or MethodWrapperDispatcher

        # like a real duck!
        self.__name__ = func.func_name

    # resolver our specials dispatchers
    def __getattr__ (self, attr):

        if attr in self.specials:
            return self.specials[attr] (self, self.instance, self.cls)

        raise AttributeError()
    
    # MOST important here: descriptor to bind our dispatcher to an instance and a class
    def __get__ (self, instance, cls = None):

        # bind ourself to pass to our specials
        self.cls = cls
        self.instance = instance

        return self.dispatcher(self, instance, cls)


class MethodWrapperDispatcher (object):

    def __init__ (self, wrapper, instance, cls):

        self.wrapper  = wrapper
        self.func     = wrapper.func
        self.instance = instance
        self.cls      = cls

        # go duck, go!
        self.bound_name = "<bound method %s.%s.begin of %s>" % (self.cls.__name__,
                                                                self.func.func_name,
                                                                repr(self.instance))

        self.unbound_name = "<unbound method %s.%s>" % (self.cls.__name__, self.func.func_name)

    def __repr__ (self):
        if self.instance:
            return self.bound_name
        else:
            return self.unbound_name
        

    def  __call__ (self, *args, **kwargs):

        # handle unbound cases (with or without instance as first argument)
        if not self.instance:

            if not args:
                args = [None, None]
                
            if not isinstance(args[0], self.cls):
                raise TypeError("unbound method %s object must be called with %s instance "
                                "as first argument (got %s instance instead)" % (self.func.func_name, self.cls.__name__,
                                                                                 args[0].__class__.__name__))
            else:
                return self.call(args[0], *args[1:], **kwargs)

        #log.debug("[calling] %s %s" % (self.instance, self.func.__name__))

        return self.call(self.instance, *args, **kwargs)

    # override this to implement custom behaviour (default just wrap without tricks)
    def call (self, *args, **kwargs):
        return self.func (*args, **kwargs)
