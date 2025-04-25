# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.filterwheel import FilterWheel, InvalidFilterPositionException
from chimera.core.lock import lock


class FilterWheelBase(ChimeraObject, FilterWheel):

    def __init__(self):
        ChimeraObject.__init__(self)

    @lock
    def set_filter(self, filter):
        raise NotImplementedError()

    def get_filter(self):
        raise NotImplementedError()

    def get_filters(self):
        return self["filters"].upper().split()

    def _get_filter_name(self, index):
        try:
            return self.get_filters()[index]
        except (ValueError, TypeError):
            raise InvalidFilterPositionException(f"Unknown filter ({str(index)}).")

    def _get_filter_position(self, name):
        return self.get_filters().index(name)

    def get_metadata(self, request):
        return [
            ("FWHEEL", str(self["filter_wheel_model"]), "Filter Wheel Model"),
            ("FILTER", str(self.get_filter()), "Filter used for this observation"),
        ]
