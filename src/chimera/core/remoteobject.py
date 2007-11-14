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


try:
    import Pyro.core
    import Pyro.constants
except ImportError, e:
    raise RuntimeError ("You must have Pyro version >= 3.6 installed.")


import time
import sys

from types import StringType


__all__ = ['RemoteObject']


class RemoteObject (Pyro.core.ObjBase):

    def __init__ (self):
        Pyro.core.ObjBase.__init__ (self)

        self.__lastUsed = None

        self.daemon = None

    def __ping__ (self):
        return 1

    def getProxy (self):

        if not self.daemon:
            return False

        return self.daemon.getProxyForObj(self)

    def Pyro_dyncall(self, method, flags, args):
        # overrride here to allow composed attributes (name.begin name.end)

        # update the timestamp
        self.__lastUsed = time.time()

        # find the method in this object, and call it with the supplied args.
        keywords = {}

        if flags & Pyro.constants.RIF_Keywords:
            # reconstruct the varargs from a tuple like
            #  (a,b,(va1,va2,va3...),{kw1:?,...})
            keywords = args[-1]
            args = args[:-1]
            
        if flags & Pyro.constants.RIF_Varargs:
            # reconstruct the varargs from a tuple like (a,b,(va1,va2,va3...))
            args = args[:-1] + args[-1]

        # If the method is part of ObjBase, never call the delegate object because
        # that object doesn't implement that method. If you don't check this,
        # remote attributes won't work with delegates for instance, because the
        # delegate object doesn't implement _r_xa. (remote_xxxattr)
        if method in dir(Pyro.core.ObjBase):
            return getattr(self, method) (*args, **keywords)

        else:

            # try..except to deal with obsoleted string exceptions (raise "blahblah")
            try :

                # object name can be composed name1.name2 to allow events and async pattern
                # so, check if this is a camposed call and look for name2 on name1 indeed.
                target = method.split (".")

                if len(target) == 1:
                    return getattr(self, method) (*args, **keywords)
                elif len(target) == 2:
                    tmp = getattr (self, target[0])

                    if target[1] in dir(tmp):
                        return getattr (tmp, target[1]) (*args, **keywords)
                else:
                    raise Exception ("Invalid method %s." % method)

            except :
                exc_info = sys.exc_info()
                try:
                    if type(exc_info[0]) == StringType :
                        if exc_info[1] == None :
                            raise Exception, exc_info[0], exc_info[2]
                        else :
                            raise Exception, "%s: %s" % (exc_info[0], exc_info[1]), exc_info[2]
                    else :
                        raise
                finally:
                    del exc_info   # delete frame to allow proper GC


