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

from chimera.interfaces.cameradriver import Device


class IFilterWheelDriver(Interface):

    __config__ = {"device": Device.USB}

    def getFilter (self):
        """
        Returns the current filter position starting with 0.
        
        @rtype: int
        """

    def setFilter (self, filter):
        """
        Set current filter.

        @param filter: Filter position starting in 0.
        @type  filter: int
        """

    @event
    def filterChange (self, newFilter, oldFilter):
        pass

