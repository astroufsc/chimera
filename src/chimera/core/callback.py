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


import sha
import time
import random

from chimera.core.chimeraobject import ChimeraObject


__all__ = ['callback']


def callback (manager):
    """Callback decorator.
    Use this decorator to add an callback object to an active Manager.
    This decorator returns a ProxyMethod that you use to subscribe to an event (using += operator)

    >>> @callback(managerInstance)
    >>> def clbk ():
    ...    print 'foo'

    >>> obj.fooComplete += clbk

    @param manager: Manager instance.
    @type manager: Manager

    @returns: ProxyMethod that wraps the decorated function.
    @rtype: ProxyMethod
    """

    class Callback (ChimeraObject):
        def __init__ (self):
            ChimeraObject.__init__(self)

    def clbk_deco (f):
        setattr(Callback, 'handler', staticmethod(f))
        return manager.addClass(Callback, 
                                'h'+sha.sha(str(time.time())+str(random.random())).hexdigest(),
                                start=False).handler

    return clbk_deco
