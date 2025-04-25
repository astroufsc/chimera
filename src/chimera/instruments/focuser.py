# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock

from chimera.interfaces.focuser import (
    Focuser,
    FocuserAxis,
    AxisControllable,
    InvalidFocusPositionException,
)


class FocuserBase(ChimeraObject, Focuser):
    def __init__(self):
        ChimeraObject.__init__(self)

        self._supports = {}

    @lock
    def move_in(self, n, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def move_out(self, n, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def move_to(self, position, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def get_position(self, axis=FocuserAxis.Z):
        raise NotImplementedError()

    def get_range(self, axis=FocuserAxis.Z):
        raise NotImplementedError()

    def get_temperature(self):
        raise NotImplementedError()

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            self.log.info(f"Invalid feature: {str(feature)}")
            return False

    def _check_axis(self, axis):
        if not self.supports(AxisControllable[axis]):
            raise InvalidFocusPositionException(f"Cannot move {axis} axis.")

    def get_metadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        md = [
            ("FOCUSER", str(self["model"]), "Focuser Model"),
            (
                "FOCUS",
                self.get_position(),
                "Focuser position used for this observation",
            ),
        ]
        try:
            md += [
                (
                    "FOCUSTEM",
                    self.get_temperature(),
                    "Focuser Temperature at Exposure End [deg. C]",
                )
            ]
        except NotImplementedError:
            pass

        return md
