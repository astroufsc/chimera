# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException
from chimera.core.lock import lock
from chimera.interfaces.filterwheel import (
    FilterWheel,
    FocusOffsetException,
    InvalidFilterPositionException,
)


class FilterWheelBase(ChimeraObject, FilterWheel):
    def __init__(self):
        ChimeraObject.__init__(self)

        # parsed lazily: __config__ is only populated after __init__, and
        # drivers are not required to chain up to our __start__
        self._focus_offsets = None
        # offset currently on the focuser; None until the first filter change
        self._applied_focus_offset = None

        # here rather than in __start__: legacy drivers override __start__
        # without chaining up, and they are exactly the ones being warned about
        self._warn_if_set_filter_overridden()

    def __start__(self):
        self.get_focus_offsets()  # fail early on a malformed offset table

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

        old_filter = self._current_filter_or_none()

        self._set_filter(filter_name)

        try:
            self._apply_focus_offset(filter_name, old_filter)
        finally:
            self.filter_change(filter_name, old_filter)

        return True

    def get_filter(self):
        raise NotImplementedError()

    def get_filters(self):
        return self["filters"].split()

    def get_focus_offsets(self):
        if self._focus_offsets is None:
            self._focus_offsets = self._parse_focus_offsets()
        return dict(self._focus_offsets)

    def _current_filter_or_none(self):
        try:
            return self.get_filter()
        except ChimeraException:
            # position unknown, e.g. a wheel that hasn't homed since power-up
            return None

    def _parse_focus_offsets(self):
        offsets = {}

        for entry in str(self["focus_offsets"] or "").split():
            name, _, value = entry.partition(":")
            try:
                offsets[name] = int(round(float(value)))
            except ValueError:
                raise FocusOffsetException(
                    f"Invalid focus_offsets entry '{entry}', expected 'FILTER:OFFSET'."
                )

        unknown = sorted(set(offsets) - set(self.get_filters()))
        if unknown:
            raise FocusOffsetException(
                f"focus_offsets names filters that are not on this wheel: {unknown}."
            )

        return offsets

    def _apply_focus_offset(self, new_filter, old_filter):
        if not self["focuser"]:
            return

        offsets = self.get_focus_offsets()
        target = offsets.get(new_filter, 0)

        applied = self._applied_focus_offset
        if applied is None:
            # first change after start-up: assume the focuser already sits
            # where the outgoing filter wants it, so only move the difference
            applied = offsets.get(old_filter, 0)

        delta = target - applied

        if delta:
            try:
                focuser = self.get_proxy(self["focuser"])
                if delta < 0:
                    self.log.debug(
                        f"Moving focuser {-delta} IN for filter {new_filter}"
                    )
                    focuser.move_in(-delta)
                else:
                    self.log.debug(
                        f"Moving focuser {delta} OUT for filter {new_filter}"
                    )
                    focuser.move_out(delta)
            except Exception as e:
                # leave _applied_focus_offset alone: it still describes the
                # last offset we know reached the focuser
                message = (
                    f"Could not apply a {delta} focus offset for filter "
                    f"{new_filter}: {e}"
                )
                if self["focus_offset_required"]:
                    raise FocusOffsetException(message) from e
                self.log.error(message)
                return

        self._applied_focus_offset = target

    def _warn_if_set_filter_overridden(self):
        """
        Drivers written against chimera <= 0.2 implement set_filter() instead
        of _set_filter(), which bypasses the focus offset entirely.
        """
        for cls in type(self).__mro__:
            if cls is FilterWheelBase:
                return
            if "set_filter" in cls.__dict__:
                self.log.warning(
                    f"{cls.__name__} overrides set_filter(): focus offsets will "
                    f"NOT be applied. Rename it to _set_filter() and drop the "
                    f"filter validation and the filter_change() call, which "
                    f"FilterWheelBase now does."
                )
                return

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

        if self["focuser"] and self._applied_focus_offset is not None:
            md += [
                (
                    "FOCUSOFF",
                    self._applied_focus_offset,
                    "Filter focus offset applied [focuser units]",
                )
            ]

        return md
