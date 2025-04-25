# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import time
import threading

from chimera.interfaces.telescope import (
    SlewRate,
    TelescopeStatus,
    TelescopeCover,
    TelescopePier,
    TelescopePierSide,
)
from chimera.instruments.telescope import TelescopeBase, ObjectTooLowException

from chimera.core.lock import lock

from chimera.util.coord import Coord
from chimera.util.position import Position, Epoch


class FakeTelescope(TelescopeBase, TelescopeCover, TelescopePier):

    def __init__(self):
        TelescopeBase.__init__(self)

        self.__slewing = False
        self._az = Coord.from_dms(0)
        self._alt = Coord.from_dms(70)

        self._slewing = False
        self._tracking = True
        self._parked = False

        self._abort = threading.Event()

        self._epoch = Epoch.J2000

        self._cover = False
        self._pier_side = TelescopePierSide.UNKNOWN

        self._ra = Position.from_ra_dec(0, 0).ra
        self._dec = Position.from_ra_dec(0, 0).dec
        self._alt = Position.from_alt_az(0, 0).alt
        self._az = Position.from_alt_az(0, 0).az

    def _set_alt_az_from_ra_dec(self):
        alt_az = self._get_site().ra_dec_to_alt_az(
            Position.from_ra_dec(self._ra, self._dec)
        )
        self._alt = alt_az.alt
        self._az = alt_az.az

    def _get_site(self):
        # FIXME: create the proxy directly and cache it
        return self.get_manager().get_proxy("/Site/0")

    def _set_ra_dec_from_alt_az(self):
        ra_dec = self._get_site().alt_az_to_ra_dec(
            Position.from_alt_az(self._alt, self._az)
        )
        self._ra = ra_dec.ra
        self._dec = ra_dec.dec

    def __start__(self):
        self.set_hz(1)

    @lock
    def control(self):
        self._get_site()
        if not self._slewing:
            if self._tracking:
                self._set_alt_az_from_ra_dec()
                try:
                    self._validate_alt_az(self.get_position_alt_az())
                except ObjectTooLowException as msg:
                    self.log.exception(msg)
                    self._stop_tracking()
                    self.tracking_stopped(
                        self.get_position_ra_dec(), TelescopeStatus.OBJECT_TOO_LOW
                    )
            else:
                self._set_ra_dec_from_alt_az()
        return True

    def slew_to_ra_dec(self, position):

        if not isinstance(position, Position):
            position = Position.from_ra_dec(position[0], position[1], epoch=Epoch.J2000)

        self._validate_ra_dec(position)

        self.slew_begin(position)

        ra_steps = position.ra - self.get_ra()
        ra_steps = float(ra_steps / 10.0)

        dec_steps = position.dec - self.get_dec()
        dec_steps = float(dec_steps / 10.0)

        self._slewing = True
        self._epoch = position.epoch
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

        self.slew_complete(self.get_position_ra_dec(), status)

    @lock
    def slew_to_alt_az(self, position):

        if not isinstance(position, Position):
            position = Position.from_alt_az(*position)

        self._validate_alt_az(position)

        self.slew_begin(self._get_site().alt_az_to_ra_dec(position))

        alt_steps = position.alt - self.get_alt()
        alt_steps = float(alt_steps / 10.0)

        az_steps = position.az - self.get_az()
        az_steps = float(az_steps / 10.0)

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

        self.slew_complete(self.get_position_ra_dec(), status)

    def abort_slew(self):
        self._abort.set()
        while self.is_slewing():
            time.sleep(0.1)

        self._slewing = False

    def is_slewing(self):
        return self._slewing

    @lock
    def move_east(self, offset, rate=SlewRate.MAX):

        self._slewing = True

        pos = self.get_position_ra_dec()
        pos = Position.from_ra_dec(pos.ra + Coord.from_as(offset), pos.dec)
        self.slew_begin(pos)

        self._ra += Coord.from_as(offset)
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self.get_position_ra_dec(), TelescopeStatus.OK)

    @lock
    def move_west(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.get_position_ra_dec()
        pos = Position.from_ra_dec(pos.ra + Coord.from_as(-offset), pos.dec)
        self.slew_begin(pos)

        self._ra += Coord.from_as(-offset)
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self.get_position_ra_dec(), TelescopeStatus.OK)

    @lock
    def move_north(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.get_position_ra_dec()
        pos = Position.from_ra_dec(pos.ra, pos.dec + Coord.from_as(offset))
        self.slew_begin(pos)

        self._dec += Coord.from_as(offset)
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self.get_position_ra_dec(), TelescopeStatus.OK)

    @lock
    def move_south(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.get_position_ra_dec()
        pos = Position.from_ra_dec(pos.ra, pos.dec + Coord.from_as(-offset))
        self.slew_begin(pos)

        self._dec += Coord.from_as(-offset)
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self.get_position_ra_dec(), TelescopeStatus.OK)

    @lock
    def get_ra(self):
        return self._ra

    @lock
    def get_dec(self):
        return self._dec

    @lock
    def get_az(self):
        return self._az

    @lock
    def get_alt(self):
        return self._alt

    @lock
    def get_position_ra_dec(self):
        return Position.from_ra_dec(self.get_ra(), self.get_dec(), epoch=self._epoch)

    @lock
    def get_position_alt_az(self):
        return Position.from_alt_az(self.get_alt(), self.get_az())

    @lock
    def get_target_ra_dec(self):
        return Position.from_ra_dec(self.get_ra(), self.get_dec())

    @lock
    def get_target_alt_az(self):
        return Position.from_alt_az(self.get_alt(), self.get_az())

    @lock
    def sync_ra_dec(self, position):
        if not isinstance(position, Position):
            position = Position.from_ra_dec(*position)

        self._ra = position.ra
        self._dec = position.dec

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
        self.tracking_started(self.get_position_ra_dec())

    @lock
    def stop_tracking(self):
        self._stop_tracking()
        self.tracking_stopped(self.get_position_ra_dec(), TelescopeStatus.ABORTED)

    def _stop_tracking(self):
        self._tracking = False

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
