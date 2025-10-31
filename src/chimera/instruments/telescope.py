# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from typing import cast

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ObjectTooLowException
from chimera.core.lock import lock
from chimera.core.site import Site
from chimera.interfaces.telescope import (
    TelescopePark,
    TelescopeSlew,
    TelescopeSync,
    TelescopeTracking,
)
from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.simbad import simbad_lookup

__all__ = ["TelescopeBase"]


class TelescopeBase(
    ChimeraObject, TelescopeSlew, TelescopeSync, TelescopePark, TelescopeTracking
):

    def __init__(self):
        super().__init__()

        self._park_position = None

    # @property
    # @functools.cache
    def site(self) -> Site:
        return cast(Site, self.get_proxy("/Site/0"))

    @lock
    def slew_to_object(self, name):
        _, ra, dec, epoch = simbad_lookup(name) or (None, None, None, None)
        if ra is None or dec is None:
            raise ObjectNotFoundException(f"Object {name} not found in SIMBAD")
        self.slew_to_ra_dec(ra, dec)  # todo use epoch from simbad_lookup

    @lock
    def slew_to_ra_dec(self, ra: float, dec: float, epoch: float = 2000) -> None:
        raise NotImplementedError()

    def _validate_ra_dec(self, ra: float, dec: float):
        # TODO: remove Position dependency
        lst = self.site().lst()
        latitude = self.site()["latitude"]

        alt_az = Position.ra_dec_to_alt_az(Position.from_ra_dec(ra, dec), latitude, lst)

        return self._validate_alt_az(alt_az.alt, alt_az.az)

    def _validate_alt_az(self, alt, az):

        if alt <= self["min_altitude"]:
            raise ObjectTooLowException(
                f"Object too close to horizon (alt={alt} limit={self['min_altitude']})"
            )

        return True

    # TODO: uncomment this method when precession is implemented.
    # def _get_final_position(self, position):

    #     if str(position.epoch).lower() != str(Epoch.NOW).lower():
    #         self.log.info(f"Precessing position ({str(position)}) from {position.epoch} to current epoch.")
    #         position_now = position.precess(Epoch.NOW)
    #     else:
    #         self.log.info(f"Current position ({str(position)}), no precession needed.")
    #         position_now = position

    #     self.log.info(f"Final precessed position {str(position_now)}")

    #     return position_now

    @lock
    def slew_to_alt_az(self, alt: float, az: float) -> None:
        raise NotImplementedError()

    def abort_slew(self) -> None:
        raise NotImplementedError()

    def is_slewing(self) -> bool:
        raise NotImplementedError()

    @lock
    def move_east(self, offset: float, rate=None) -> None:
        raise NotImplementedError()

    @lock
    def move_west(self, offset: float, rate=None) -> None:
        raise NotImplementedError()

    @lock
    def move_north(self, offset: float, rate=None) -> None:
        raise NotImplementedError()

    @lock
    def move_south(self, offset: float, rate=None) -> None:
        raise NotImplementedError()

    @lock
    def move_offset(self, offset_ra: float, offset_dec: float, rate=None) -> None:

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
        if ra is None or dec is None:
            raise ObjectNotFoundException(f"Object {name} not found in SIMBAD")
        self.sync_ra_dec(ra, dec, epoch=epoch)

    @lock
    def sync_ra_dec(self, ra: float, dec: float, epoch: float = 2000) -> None:
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
        ra, dec = self.get_position_ra_dec()
        alt, az = self.get_position_alt_az()
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
                str(Coord.from_h(ra).to_hms()),
                "Right ascension of the observed object",
            ),
            (
                "DEC",
                str(Coord.from_d(dec).to_dms()),
                "Declination of the observed object",
            ),
            ("EQUINOX", "NOW", "coordinate epoch"),
            ("ALT", str(Coord.from_d(alt).to_dms()), "Altitude of the observed object"),
            ("AZ", str(Coord.from_d(az).to_dms()), "Azimuth of the observed object"),
            ("AIRMASS", alt.radian, "Airmass of the observed object"),
            ("WCSAXES", 2, "wcs dimensionality"),
            ("RADESYS", "ICRS", "frame of reference"),
            (
                "CRVAL1",
                Coord.from_h(ra).deg,
                "coordinate system value at reference pixel",
            ),
            (
                "CRVAL2",
                Coord.from_d(dec).deg,
                "coordinate system value at reference pixel",
            ),
            ("CTYPE1", "RA---TAN", "name of the coordinate axis"),
            ("CTYPE2", "DEC--TAN", "name of the coordinate axis"),
            ("CUNIT1", "deg", "units of coordinate value"),
            ("CUNIT2", "deg", "units of coordinate value"),
        ]
