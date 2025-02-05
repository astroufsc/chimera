# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.instruments.filterwheel import FilterWheelBase
from chimera.core.lock import lock


class FakeFilterWheel(FilterWheelBase):

    def __init__(self):
        FilterWheelBase.__init__(self)

        self._lastFilter = 0

    def getFilter(self):
        return self._getFilterName(self._lastFilter)

    @lock
    def setFilter(self, filter):

        filterName = str(filter).upper()

        if filterName not in self.getFilters():
            raise InvalidFilterPositionException(f"Invalid filter {filter}.")

        self.filterChange(filter, self._getFilterName(self._lastFilter))

        self._lastFilter = self._getFilterPosition(filter)
