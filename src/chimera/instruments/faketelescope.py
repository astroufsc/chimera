# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import threading
import time
from typing import override

from chimera.core.lock import lock
from chimera.instruments.telescope import ObjectTooLowException, TelescopeBase
from chimera.interfaces.telescope import (
    TelescopePier,
    TelescopePierSide,
    TelescopeStatus,
)
from chimera.util.coord import Coord
from chimera.util.position import Epoch, Position


class FakeTelescope(TelescopeBase, TelescopePier):
    def __init__(self):
        TelescopeBase.__init__(self)

        self._az = 0
        self._alt = 0

        self._slewing = False
        self._tracking = False
        self._parked = False

        self._abort = threading.Event()

        self._epoch = 2000.0  # Default epoch for RA/Dec

        self._cover = False
        self._pier_side = TelescopePierSide.UNKNOWN

        self._ra: float = 0.0
        self._dec: float = 0.0
        self._alt: float = 0.0
        self._az: float = 0.0

    def _set_alt_az_from_ra_dec(self):
        alt_az = self._get_site().ra_dec_to_alt_az(
            Position.from_ra_dec(Coord.from_h(self._ra), Coord.from_d(self._dec))
        )
        self._alt = float(alt_az.alt)
        self._az = float(alt_az.az)

    def _get_site(self):
        # FIXME: create the proxy directly and cache it
        return self.get_proxy("/Site/0")

    def _set_ra_dec_from_alt_az(self):
        ra_dec = self._get_site().alt_az_to_ra_dec(
            Position.from_alt_az(Coord.from_d(self._alt), Coord.from_d(self._az))
        )
        self._ra = float(ra_dec.ra.to_h())
        self._dec = float(ra_dec.dec.to_d())

    def __start__(self):
        self.set_hz(1)

    def control(self):
        if not self._slewing:
            if self._tracking:
                self._set_alt_az_from_ra_dec()
                try:
                    self._validate_alt_az(self.get_alt(), self.get_az())
                except ObjectTooLowException as msg:
                    self.log.exception(msg)
                    self.stop_tracking()
                    self.tracking_stopped(TelescopeStatus.OBJECT_TOO_LOW)
            else:
                self._set_ra_dec_from_alt_az()
        return True

    def slew_to_ra_dec(self, ra: float, dec: float, epoch=None):

        # TODO: remove checks after Position dependency is removed
        if epoch is None:
            epoch = 2000
        elif not isinstance(epoch, float):
            raise TypeError(f"Epoch must be a float, got {type(epoch)}")
        if epoch != 2000.0:
            raise NotImplementedError(f"Only J2000 epoch is supported. Epoch: {epoch}")

        self._validate_ra_dec(ra, dec)

        self.slew_begin(ra, dec)

        ra_steps = (ra - self.get_ra()) / 10
        dec_steps = (dec - self.get_dec()) / 10

        self._slewing = True
        self._epoch = epoch
        self._abort.clear()

        status = TelescopeStatus.OK

        t = 0
        while t < 5:

            if self._abort.is_set():
                self._slewing = False
                status = TelescopeStatus.ABORTED
                break

            self._ra += ra_steps
            self._dec += dec_steps
            self._set_alt_az_from_ra_dec()

            time.sleep(0.5)
            t += 0.5

        self._slewing = False

        self.start_tracking()

        self.slew_complete(self.get_ra(), self.get_dec(), status)

    @lock
    def slew_to_alt_az(self, alt: float, az: float):

        self._validate_alt_az(alt, az)

        pos = self._get_site().alt_az_to_ra_dec(Position.from_alt_az(alt, az))
        self.slew_begin(pos.alt, pos.az)  # todo: remove Position dependency

        alt_steps = (alt - self.get_alt()) / 10
        az_steps = (az - self.get_az()) / 10

        self._slewing = True
        self._abort.clear()

        status = TelescopeStatus.OK
        t = 0
        while t < 5:

            if self._abort.is_set():
                self._slewing = False
                status = TelescopeStatus.ABORTED
                break

            self._alt += alt_steps
            self._az += az_steps
            self._set_ra_dec_from_alt_az()

            time.sleep(0.5)
            t += 0.5

        self._slewing = False

        self.slew_complete(self.get_ra(), self.get_dec(), status)

    def abort_slew(self):
        self._abort.set()
        while self.is_slewing():
            time.sleep(0.1)

        self._slewing = False

    def is_slewing(self):
        return self._slewing

    @lock
    def move_east(self, offset, rate=None):

        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra + Coord.from_as(offset), dec, epoch=Epoch.NOW)
        self.slew_begin(pos.ra, pos.dec)

        self._ra += float(Coord.from_as(offset).to_h())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(pos.ra, pos.dec, TelescopeStatus.OK)

    @lock
    def move_west(self, offset, rate=None):
        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra + Coord.from_as(-offset), dec)
        self.slew_begin(pos.ra, pos.dec)

        self._ra += float(Coord.from_as(-offset).to_h())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(pos.ra, pos.dec, TelescopeStatus.OK)

    @lock
    def move_north(self, offset, rate=None):
        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra, dec + Coord.from_as(offset))
        self.slew_begin(pos.ra, pos.dec)

        self._dec += float(Coord.from_as(offset).to_d())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(pos.ra, pos.dec, TelescopeStatus.OK)

    @lock
    def move_south(self, offset, rate=None):
        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra, dec + Coord.from_as(-offset))
        self.slew_begin(pos.ra, pos.dec)

        self._dec += float(Coord.from_as(-offset).to_d())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(pos.ra, pos.dec, TelescopeStatus.OK)

    @lock
    @override
    def get_ra(self) -> float:
        return self._ra

    @lock
    @override
    def get_dec(self) -> float:
        return self._dec

    @lock
    def get_az(self):
        return self._az

    @lock
    def get_alt(self):
        return self._alt

    @lock
    def get_position_ra_dec(self):
        return self.get_ra(), self.get_dec()

    @lock
    def get_position_alt_az(self):
        pos = Position.from_alt_az(self.get_alt(), self.get_az())
        return pos.alt, pos.az

    @lock
    def get_target_ra_dec(self):
        return self.get_position_ra_dec()

    @lock
    def get_target_alt_az(self):
        return self.get_position_alt_az()

    @lock
    def sync_ra_dec(self, ra, dec, epoch=2000):
        if epoch is None or epoch == 2000:
            position = Position.from_ra_dec(ra, dec, epoch=Epoch.J2000)
        else:
            raise NotImplementedError("Only J2000 epoch is supported")
        # Convert to Current Epoch before syncing
        position.to_epoch(Epoch.NOW)
        self._ra = float(position.ra.to_h())
        self._dec = float(position.dec.to_d())

    @lock
    def park(self):
        self.log.info("Parking...")
        self._parked = True
        self.park_complete()

    @lock
    def unpark(self):
        self.log.info("Unparking...")
        self._parked = False
        self.unpark_complete()

    def is_parked(self):
        return self._parked

    @lock
    def start_tracking(self):
        self._tracking = True
        self.tracking_started()

    @lock
    def stop_tracking(self):
        self._tracking = False
        self.tracking_stopped(TelescopeStatus.ABORTED)

    def is_tracking(self):
        return self._tracking

    def open_cover(self):
        self._cover = True

    def close_cover(self):
        self._cover = False

    def is_cover_open(self):
        return self._cover

    def set_pier_side(self, side):
        self._pier_side = side

    def get_pier_side(self):
        return self._pier_side
