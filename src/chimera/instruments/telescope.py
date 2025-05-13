# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.telescope import (
    TelescopeSlew,
    TelescopeSync,
    TelescopePark,
    TelescopeTracking,
    SlewRate,
)

from chimera.core.lock import lock
from chimera.core.exceptions import ObjectNotFoundException, ObjectTooLowException

from chimera.util.simbad import simbad_lookup
from chimera.util.position import Epoch, Position


__all__ = ["TelescopeBase"]


class TelescopeBase(
    ChimeraObject, TelescopeSlew, TelescopeSync, TelescopePark, TelescopeTracking
):

    def __init__(self):
        ChimeraObject.__init__(self)

        self._park_position = None
        self.site = None

    @lock
    def slew_to_object(self, name):
        _, ra, dec, epoch = simbad_lookup(name) or (None, None, None, None)
        if ra is None or dec is None:
            raise ObjectNotFoundException(f"Object {name} not found in SIMBAD")
        self.slew_to_ra_dec(
            Position.from_ra_dec(ra, dec)
        )  # todo use epoch from simbad_lookup

    @lock
    def slew_to_ra_dec(self, position):
        raise NotImplementedError()

    def _validate_ra_dec(self, position):

        if self.site is None:
            self.site = self.get_manager().get_proxy("/Site/0")
        lst = self.site.lst()
        latitude = self.site["latitude"]

        alt_az = Position.ra_dec_to_alt_az(position, latitude, lst)

        return self._validate_alt_az(alt_az)

    def _validate_alt_az(self, position):

        if position.alt <= self["min_altitude"]:
            raise ObjectTooLowException(
                f"Object too close to horizon (alt={position.alt} limit={self['min_altitude']})"
            )

        return True

    def _get_final_position(self, position):

        if str(position.epoch).lower() != str(Epoch.NOW).lower():
            self.log.info(
                f"Precessing position ({str(position)}) from {position.epoch} to current epoch."
            )
            position_now = position.precess(Epoch.NOW)
        else:
            self.log.info(f"Current position ({str(position)}), no precession needed.")
            position_now = position

        self.log.info(f"Final precessed position {str(position_now)}")

        return position_now

    @lock
    def slew_to_alt_az(self, position):
        raise NotImplementedError()

    def abort_slew(self):
        raise NotImplementedError()

    def is_slewing(self):
        raise NotImplementedError()

    @lock
    def move_east(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def move_west(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def move_north(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def move_south(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def move_offset(self, offset_ra, offset_dec, rate=SlewRate.GUIDE):

        if offset_ra == 0:
            pass
        elif offset_ra > 0:
            self.move_east(offset_ra, rate)
        else:
            self.move_west(abs(offset_ra), rate)

        if offset_dec == 0:
            pass
        elif offset_dec > 0:
            self.move_north(offset_dec, rate)
        else:
            self.move_south(abs(offset_dec), rate)

    def get_ra(self):
        raise NotImplementedError()

    def get_dec(self):
        raise NotImplementedError()

    def get_az(self):
        raise NotImplementedError()

    def get_alt(self):
        raise NotImplementedError()

    def get_position_ra_dec(self):
        raise NotImplementedError()

    def get_position_alt_az(self):
        raise NotImplementedError()

    def get_target_ra_dec(self):
        raise NotImplementedError()

    def get_target_alt_az(self):
        raise NotImplementedError()

    @lock
    def sync_object(self, name):
        _, ra, dec, epoch = simbad_lookup(name) or (None, None, None, None)
        if not ra or not dec:
            raise ObjectNotFoundException(f"Object {name} not found in SIMBAD")
        self.sync_ra_dec(
            Position.from_ra_dec(ra, dec)
        )  # todo use epoch from simbad_lookup

    @lock
    def sync_ra_dec(self, position):
        raise NotImplementedError()

    @lock
    def park(self):
        raise NotImplementedError()

    @lock
    def unpark(self):
        raise NotImplementedError()

    def is_parked(self):
        raise NotImplementedError()

    @lock
    def set_park_position(self, position):
        self._park_position = position

    def get_park_position(self):
        return self._park_position or self["default_park_position"]

    def start_tracking(self):
        raise NotImplementedError()

    def stop_tracking(self):
        raise NotImplementedError()

    def is_tracking(self):
        raise NotImplementedError()

    def get_metadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.get_metadata_override(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        position = self.get_position_ra_dec()
        alt = self.get_alt()
        return [
            ("TELESCOP", self["model"], "Telescope Model"),
            ("OPTICS", self["optics"], "Telescope Optics Type"),
            ("MOUNT", self["mount"], "Telescope Mount Type"),
            ("APERTURE", self["aperture"], "Telescope aperture size [mm]"),
            ("F_LENGTH", self["focal_length"], "Telescope focal length [mm]"),
            ("F_REDUCT", self["focal_reduction"], "Telescope focal reduction"),
            # TODO: Convert coordinates to proper equinox
            # TODO: How to get ra,dec at start of exposure (not end)
            (
                "RA",
                position.ra.to_dms().__str__(),
                "Right ascension of the observed object",
            ),
            (
                "DEC",
                position.dec.to_dms().__str__(),
                "Declination of the observed object",
            ),
            ("EQUINOX", position.epoch_string()[1:], "coordinate epoch"),
            ("ALT", alt.to_dms().__str__(), "Altitude of the observed object"),
            ("AZ", self.get_az().to_dms().__str__(), "Azimuth of the observed object"),
            ("AIRMASS", alt.radian, "Airmass of the observed object"),
            ("WCSAXES", 2, "wcs dimensionality"),
            ("RADESYS", "ICRS", "frame of reference"),
            ("CRVAL1", position.ra.deg, "coordinate system value at reference pixel"),
            ("CRVAL2", position.dec.deg, "coordinate system value at reference pixel"),
            ("CTYPE1", "RA---TAN", "name of the coordinate axis"),
            ("CTYPE2", "DEC--TAN", "name of the coordinate axis"),
            ("CUNIT1", "deg", "units of coordinate value"),
            ("CUNIT2", "deg", "units of coordinate value"),
        ]
