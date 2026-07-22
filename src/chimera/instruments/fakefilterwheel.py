# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.instruments.filterwheel import FilterWheelBase


class FakeFilterWheel(FilterWheelBase):
    def __init__(self):
        FilterWheelBase.__init__(self)

        self._last_filter = 0

    def get_filter(self):
        return self._get_filter_name(self._last_filter)

    def _set_filter(self, filter_name):
        self._last_filter = self._get_filter_position(filter_name)
