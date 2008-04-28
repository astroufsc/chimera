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


from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.filterwheel import IFilterWheel
from chimera.interfaces.filterwheel import Filter
from chimera.interfaces.filterwheel import InvalidFilterPositionException

from chimera.core.lock import lock


class FilterWheel (ChimeraObject, IFilterWheel):

    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):
        drv = self.getDriver()
        drv.filterChange += self.getProxy()._filterChangeClbk
        return True

    def __stop__ (self):
        drv = self.getDriver()
        drv.filterChange -= self.getProxy()._filterChangeClbk
        return True

    def _filterChangeClbk (self, new, old):
        self.filterChange (self._getFilterName(new),
                           self._getFilterName(old))

    @lock
    def getFilter (self):
        drv = self.getDriver()
        return self._getFilterName(drv.getFilter())

    def getFilters (self):
        return self["filters"].upper().split()

    def _getFilterName (self, index):
        try:
            return self.getFilters()[index]
        except ValueError:
            self.log.warning("Driver returned an filter that I don't known the name.")
            return filter

    def _getFilterPosition (self, name):
        return self.getFilters().index(name)

    @lock
    def setFilter (self, filter):
        
        drv = self.getDriver()
        filterName = str(filter).upper()

        if filterName not in self.getFilters() :
            raise InvalidFilterPositionException("Invalid filter %s" % filterName)      

        return drv.setFilter(self._getFilterPosition(filterName))

    @lock
    def getDriver(self, lazy=True):
        return self.getManager().getProxy(self['driver'], lazy=lazy)        
        


