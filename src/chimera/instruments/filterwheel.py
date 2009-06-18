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

from chimera.interfaces.filterwheel import (IFilterWheel,
                                            InvalidFilterPositionException)

from chimera.core.lock import lock


class FilterWheelBase (ChimeraObject, IFilterWheel):

    def __init__ (self):
        ChimeraObject.__init__(self)

    @lock
    def setFilter (self, filter):
        raise NotImplementedError()

    def getFilter (self):
        raise NotImplementedError()

    def getFilters (self):
        return self["filters"].upper().split()

    def _getFilterName (self, index):
        try:
            return self.getFilters()[index]
        except (ValueError, TypeError):
           raise InvalidFilterPositionException("Unknown filter (%s)."%str(index))

    def _getFilterPosition (self, name):
        return self.getFilters().index(name)

    def getMetadata(self, request):
        return [('FWHEEL', str(self['filter_wheel_model']), 'FilterWheel Model'),
                ('FILTER', str(self.getFilter()),
                 'Filter used for this observation')]
