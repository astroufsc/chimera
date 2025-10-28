# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import astropy.units as units

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.seeingmonitor import SeeingMonitor


class SeeingBase(ChimeraObject, SeeingMonitor):
    def __init__(self):
        ChimeraObject.__init__(self)

        self._supports = {}

    def _convert_units(self, value, unit_in, unit_out, equivalencies=None):
        if unit_in == unit_out:
            return value

        return (value * unit_in).to(unit_out, equivalencies).value

    def supports(self, feature=None):
        if feature in self._supports:
            return self._supports[feature]
        else:
            self.log.info(f"Invalid feature: {str(feature)}")
            return False

    def seeing(self, unit_out=units.arcsec):
        raise NotImplementedError()

    def seeing_at_zenith(self, unit_out=units.arcsec):
        raise NotImplementedError()

    def flux(self, unit_out=units.count):
        raise NotImplementedError()

    def airmass(self, unit_out=units.dimensionless_unscaled):
        raise NotImplementedError()

    def get_metadata(self, request):
        # TODO: Check if metadata parameter is implemented or not.
        return [
            ("SEEMOD", str(self["model"]), "Seeing monitor Model"),
        ]
