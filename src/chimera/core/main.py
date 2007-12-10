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

from chimera.core.location  import Location
from chimera.core.proxy     import Proxy
from chimera.core.constants import MANAGER_LOCATION

import chimera.core.log

import logging
import string


__all__ = ['Chimera',
           'chimera']


log = logging.getLogger(__name__)


class Chimera (object):

    def __getattr__ (self, attr):

        if attr[0] not in string.ascii_uppercase:
            raise AttributeError()

        return Locator (attr)


# provide default object
chimera = Chimera()


class Locator (object):

    def __init__ (self, cls):
        self.cls = cls

    def __call__ (self, name = None, **options):

        name   = name or options.get ('name', '0')
        host   = options.get ('host', None)
        port   = options.get ('port', None)
        config = options.get ('config', {})

        # contact 'cls' manager (could be ourself)
        manager = Proxy(location=MANAGER_LOCATION, host=host, port=port)

        loc = Location(cls = self.cls, name = name, config = config)
       
        if not manager.ping():
            log.warning ("Can't contact '%s' manager at '%s'." % (loc, manager.URI.address))
            return False
        
        proxy = manager.getProxy(loc)

        if not proxy:
            log.warning ("There is no '%s' object at '%s'." % (loc, manager.URI.address))
            return False
        else:
            return proxy

