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
    def moveIn(self, n, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def moveOut(self, n, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def moveTo(self, position, axis=FocuserAxis.Z):
        raise NotImplementedError()

    @lock
    def getPosition(self, axis=FocuserAxis.Z):
        raise NotImplementedError()

    def getRange(self, axis=FocuserAxis.Z):
        raise NotImplementedError()

    def getTemperature(self):
        raise NotImplementedError()

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            self.log.info(f"Invalid feature: {str(feature)}")
            return False

    def _checkAxis(self, axis):
        if not self.supports(AxisControllable[axis]):
            raise InvalidFocusPositionException(f"Cannot move {axis} axis.")

    def getMetadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.getMetadataOverride(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        md = [
            ("FOCUSER", str(self["model"]), "Focuser Model"),
            ("FOCUS", self.getPosition(), "Focuser position used for this observation"),
        ]
        try:
            md += [
                (
                    "FOCUSTEM",
                    self.getTemperature(),
                    "Focuser Temperature at Exposure End [deg. C]",
                )
            ]
        except NotImplementedError:
            pass

        return md
