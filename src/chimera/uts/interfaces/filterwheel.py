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

from uts.core.interface import Interface
from uts.core.event import event

class IFilterWheel(Interface):

    __options__ = {"driver" : "/SBIG/sbig",
                   "filters": ["red", "green", "blue", "rgb", "clear"],
                   "red"    : 1,
                   "green"  : 2,
                   "blue"   : 3,
                   "rgb"    : 4,
                   "clear"  : 5}

    # filter status
    unknown = 0
    idle    = 1
    busy    = 2

    # methods
    def getFilter (self):
        pass

    def setFilter (self, _filter):
        pass
        
    def getFilterStatus (self):
        pass

    # events
    @event
    def filterChanged(self, newFilter, oldFilter):
        pass

class IFilterWheelDriver(Interface):

    def getFilter (self):
        pass

    def setFilter (self, _filter):
        pass
        
    def getFilterStatus (self):
        pass

    @event
    def filterChanged(self, newFilter, oldFilter):
        pass

