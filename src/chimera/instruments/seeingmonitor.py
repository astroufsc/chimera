# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.seeingmonitor import SeeingMonitor
import astropy.units as units


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
            self.log.info("Invalid feature: %s" % str(feature))
            return False

    def seeing(self, unit_out=units.arcsec):
        raise NotImplementedError()

    def seeing_at_zenith(self, unit_out=units.arcsec):
        raise NotImplementedError()

    def flux(self, unit_out=units.count):
        raise NotImplementedError()

    def airmass(self, unit_out=units.dimensionless_unscaled):
        raise NotImplementedError()

    def getMetadata(self, request):
        # TODO: Check if metadata parameter is implemented or not.
        return [
            ("SEEMOD", str(self["model"]), "Seeing monitor Model"),
        ]
