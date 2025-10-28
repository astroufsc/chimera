# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.lock import lock
from chimera.instruments.filterwheel import FilterWheelBase
from chimera.interfaces.filterwheel import InvalidFilterPositionException


class FakeFilterWheel(FilterWheelBase):

    def __init__(self):
        FilterWheelBase.__init__(self)

        self._last_filter = 0

    def get_filter(self):
        return self._get_filter_name(self._last_filter)

    @lock
    def set_filter(self, filter):

        filter_name = str(filter).upper()

        if filter_name not in self.get_filters():
            raise InvalidFilterPositionException(f"Invalid filter {filter}.")

        self.filter_change(filter, self._get_filter_name(self._last_filter))

        self._last_filter = self._get_filter_position(filter)
