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


from chimera.core.constants import MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT, MANAGER_LOCATION

try:
    import Pyro.core
except ImportError, e:
    raise RuntimeError ("You must have Pyro version >= 3.6 installed.")

def getManagerURI (host = None, port = None):

    host = host or MANAGER_DEFAULT_HOST
    port = port or MANAGER_DEFAULT_PORT
    
    return Pyro.core.PyroURI(host, MANAGER_LOCATION, port)


