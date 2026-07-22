# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface


class InvalidFilterPositionException(ChimeraException):
    pass


class FocusOffsetException(ChimeraException):
    """
    Raised when the focus offset of a filter could not be applied.
    """


class FilterWheel(Interface):
    """
    An interface for electromechanical filter wheels.
    Allow simple control and monitor filter changes
    """

    __config__ = {
        "device": "/dev/ttyS0",
        "filter_wheel_model": "Fake Filters Inc.",
        "filters": "R G B LUNAR CLEAR",  # space separated filter names (in position order)
        # Focuser used to compensate for the different optical thickness of
        # each filter. Leave as None (the default) to disable compensation.
        "focuser": None,
        # Focus offsets in the focuser's own units (steps, microns, ...),
        # as "FILTER:OFFSET" pairs, e.g.
        # "U:-100 B:0 V:0". Filters absent from the table get no offset.
        "focus_offsets": "",
        # Fail the filter change when the focus offset cannot be applied. Set
        # to false to only log the error and carry on. Only real YAML booleans
        # work here, not the strings "true"/"false" (astroufsc/chimera#258).
        "focus_offset_required": True,
    }

    def set_filter(self, filter):
        """
        Set the current filter, applying the configured focus offset (if any)
        before returning.

        @param filter: The filter to use.
        @type  filter: str

        @raises InvalidFilterPositionException: When the filter is not
        available on this wheel.

        @raises FocusOffsetException: When the focus offset could not be
        applied and C{focus_offset_required} is set.

        @rtype: None
        """

    def get_filter(self):
        """
        Return the current filter.

        @return: Current filter.
        @rtype: str
        """

    def get_filters(self):
        """
        Return a tuple with the available filter on this wheel.

        @return: Tuple of all filters available.
        @rtype: tuple
        """

    def get_focus_offsets(self):
        """
        Return the configured focus offsets, in the focuser's own units,
        keyed by filter
        name. Filters with no configured offset are absent from the mapping.

        @return: Focus offset of each filter.
        @rtype: dict
        """

    @event
    def filter_change(self, new_filter, old_filter):
        """
        Fired when the wheel changes the current filter.

        @param new_filter: The new current filter.
        @type  new_filter: str

        @param old_filter: The last filter.
        @type  old_filter: str
        """
