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


from chimera.core.interface import Interface
from chimera.core.event import event

from chimera.core.exceptions import ChimeraException

class InvalidFilterPositionException (ChimeraException):
    pass

class FilterWheel (Interface):
    """ An interface for electromechanical filter wheels.

    Allow simple control and monitor filter changes    
    """

    __config__ = {"device": "/dev/ttyS0",
                  "filter_wheel_model"   : "Fake Filters Inc.",
                  "filters" : "R G B LUNAR CLEAR" # space separated
                                                  # filter names (in position order)
                  }
    

    def setFilter (self, filter):
        """Set the current filter.

        @param filter: The filter to use.
        @type  filter: str

        @rtype: None
        """

    def getFilter (self):
        """Return the current filter.

        @return: Current filter.
        @rtype: str
        """

    def getFilters (self):
        """Return a tuple with the available filter on this wheel.

        @return: Tuple of all filters available.
        @rtype: tuple
        """

    @event
    def filterChange (self, newFilter, oldFilter):
        """Fired when the wheel changes the current filter.

        @param newFilter: The new current filter.
        @type  newFilter: str

        @param oldFilter: The last filter.
        @type  oldFilter: str
        """
