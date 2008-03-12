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
from chimera.util.enum  import Enum

from chimera.core.exceptions import ChimeraException


Filter = Enum ("U", "B", "V", "R", "I",  # Johnson-Cousins
               "C", "M", "T1", "T2",     # Washington
               "u", "g", "r", "i", "z",  # SDSS
               "J", "H", "K", "Kp",      # MKO
               "Z", "Y", "J", "H", "K",  # UKIDSS design

               "R", "G", "B", "RGB",
               "RED", "GREEN", "BLUE",
               "H_ALPHA", "H_BETA",
               "CLEAR", "LUNAR",
               )

class InvalidFilterPositionException (ChimeraException):
    pass


class IFilterWheel (Interface):
    """ An interface for electromechanical filter wheels.

    Allow simple control and monitor filter changes    
    """

    __config__ = {"driver"  : "/SBIG/sbig",
                  "model"   : "Fake Filters Inc.",
                  "filters" : "R G B CLEAR LUNAR" # space or comma separated
                                                  # filter names (in position order)
                  }
    

    def setFilter (self, filter):
        """Set the current filter.

        @param filter: The filter to use.
        @type  filter: L{Filter} or str

        @rtype: None
        """

    def getFilter (self):
        """Return the current filter.


        @return: Current filter.
        @rtype: L{Filter}
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
        @type  newFilter: L{Filter}

        @param oldFilter: The last filter.
        @type  oldFilter: L{Filter}
        """
