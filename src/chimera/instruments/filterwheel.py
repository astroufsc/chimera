# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.interfaces.filterwheel import (
    FilterWheel,
    FocusOffsetException,
    InvalidFilterPositionException,
)


class FilterWheelBase(ChimeraObject, FilterWheel):
    def __init__(self):
        ChimeraObject.__init__(self)

        # validated at __start__; empty until then so get_metadata() before
        # start-up (and drivers that skip our __start__) still work
        self._focus_offsets = {}

    def __start__(self):
        self._focus_offsets = self._validate_focus_offsets()

    def _set_filter(self, filter_name):
        """
        Move the wheel to filter_name. Called with the object monitor held and
        with filter_name already validated against the configured filters.

        Drivers implement this; the focus offset, the C{filter_change} event
        and the validation are handled by L{set_filter}.
        """
        raise NotImplementedError()

    @lock
    def set_filter(self, filter):
        filter_name = str(filter)

        if filter_name not in self.get_filters():
            raise InvalidFilterPositionException(f"Invalid filter {filter}.")

        old_filter = self.get_filter()

        self._set_filter(filter_name)

        try:
            self._apply_focus_offset(filter_name, old_filter)
        finally:
            self.filter_change(filter_name, old_filter)

        return True

    def get_filter(self):
        raise NotImplementedError()

    def get_filters(self):
        return list(self["filters"] or [])

    def _validate_focus_offsets(self):
        offsets = self["focus_offsets"] or {}

        normalized = {}
        for name, value in offsets.items():
            try:
                normalized[name] = int(round(float(value)))
            except (TypeError, ValueError):
                raise FocusOffsetException(
                    f"Invalid focus_offsets value for filter '{name}': {value!r}."
                )

        unknown = sorted(set(normalized) - set(self.get_filters()))
        if unknown:
            raise FocusOffsetException(
                f"focus_offsets names filters that are not on this wheel: {unknown}."
            )

        return normalized

    def _apply_focus_offset(self, new_filter, old_filter):
        if not self["focuser"]:
            return

        offsets = self._focus_offsets
        # relative move: only the difference between the outgoing and the
        # incoming filter. An unknown/unhomed old_filter contributes no offset.
        delta = offsets.get(new_filter, 0) - offsets.get(old_filter, 0)

        if not delta:
            return

        try:
            focuser = self.get_proxy(self["focuser"])
            if delta < 0:
                self.log.debug(f"Moving focuser {-delta} IN for filter {new_filter}")
                focuser.move_in(-delta)
            else:
                self.log.debug(f"Moving focuser {delta} OUT for filter {new_filter}")
                focuser.move_out(delta)
        except Exception as e:
            raise FocusOffsetException(
                f"Could not apply a {delta} focus offset for filter {new_filter}: {e}"
            ) from e

    def _get_filter_name(self, index):
        try:
            return self.get_filters()[index]
        except (ValueError, TypeError):
            raise InvalidFilterPositionException(f"Unknown filter ({str(index)}).")

    def _get_filter_position(self, name):
        return self.get_filters().index(name)

    def get_metadata(self, request):
        md = self.get_metadata_override(request)
        if md is not None:
            return md

        md = [
            ("FWHEEL", str(self["filter_wheel_model"]), "Filter Wheel Model"),
            ("FILTER", str(self.get_filter()), "Filter used for this observation"),
        ]

        if self["focuser"]:
            md += [
                (
                    "FOCUSOFF",
                    self._focus_offsets.get(self.get_filter(), 0),
                    "Filter focus offset applied [focuser units]",
                )
            ]

        return md
