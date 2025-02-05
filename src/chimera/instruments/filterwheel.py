# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.filterwheel import FilterWheel, InvalidFilterPositionException
from chimera.core.lock import lock


class FilterWheelBase(ChimeraObject, FilterWheel):

    def __init__(self):
        ChimeraObject.__init__(self)

    @lock
    def setFilter(self, filter):
        raise NotImplementedError()

    def getFilter(self):
        raise NotImplementedError()

    def getFilters(self):
        return self["filters"].upper().split()

    def _getFilterName(self, index):
        try:
            return self.getFilters()[index]
        except (ValueError, TypeError):
            raise InvalidFilterPositionException(f"Unknown filter ({str(index)}).")

    def _getFilterPosition(self, name):
        return self.getFilters().index(name)

    def getMetadata(self, request):
        return [
            ("FWHEEL", str(self["filter_wheel_model"]), "FilterWheel Model"),
            ("FILTER", str(self.getFilter()), "Filter used for this observation"),
        ]
