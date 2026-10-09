# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import math
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
        #: Set by `set_pier_side`, cleared by a slew. None means "derive it".
        self._pier_side_override = None

        self._ra: float = 0.0
        self._dec: float = 0.0
        self._alt: float = 0.0
        self._az: float = 0.0

    def _set_alt_az_from_ra_dec(self):
        self._alt, self._az = self.get_site().ra_dec_to_alt_az(self._ra, self._dec)

    def _set_ra_dec_from_alt_az(self):
        # alt, az in degrees
        self._ra, self._dec = self.get_site().alt_az_to_ra_dec(self._alt, self._az)

    def __start__(self):
        self.set_hz(1)

    def _control(self):
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

        # A slew picks its own branch, so a pinned side stops applying.
        self._pier_side_override = None
        self.slew_begin(ra, dec, epoch)

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

        ra, dec = self.get_site().alt_az_to_ra_dec(alt, az)
        # A slew picks its own branch, so a pinned side stops applying.
        self._pier_side_override = None
        self.slew_begin(ra, dec)

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
        self._jog_ra(float(Coord.from_as(offset).to_h()))

    @lock
    def move_west(self, offset, rate=None):
        self._jog_ra(-float(Coord.from_as(offset).to_h()))

    def _jog_ra(self, offset):
        # offset in hours. RA is a clock: a jog either side of 0 h wraps, it
        # does not run off the end into a Position that refuses to be built
        self._slewing = True

        ra = (self.get_ra() + offset) % 24
        # A slew picks its own branch, so a pinned side stops applying.
        self._pier_side_override = None
        self.slew_begin(ra, self.get_dec())

        self._ra = ra
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self._ra, self._dec, TelescopeStatus.OK)

    @lock
    def move_north(self, offset, rate=None):
        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra, dec + Coord.from_as(offset))
        # A slew picks its own branch, so a pinned side stops applying.
        self._pier_side_override = None
        self.slew_begin(float(pos.ra), float(pos.dec))

        self._dec += float(Coord.from_as(offset).to_d())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self._ra, self._dec, TelescopeStatus.OK)

    @lock
    def move_south(self, offset, rate=None):
        self._slewing = True

        ra, dec = self.get_position_ra_dec()
        pos = Position.from_ra_dec(ra, dec + Coord.from_as(-offset))
        # A slew picks its own branch, so a pinned side stops applying.
        self._pier_side_override = None
        self.slew_begin(float(pos.ra), float(pos.dec))

        self._dec += float(Coord.from_as(-offset).to_d())
        self._set_alt_az_from_ra_dec()

        self._slewing = False
        self.slew_complete(self._ra, self._dec, TelescopeStatus.OK)

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
        return float(pos.alt), float(pos.az)

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
        """Pin the reported side, overriding what the position implies.

        Kept because `chimera tel --pier-side-east/west` calls it. The override
        is cleared by the next slew, which is what a real mount does: it picks
        its own branch on the way to the target.
        """
        self._pier_side_override = side

    def get_pier_side(self):
        """The MECHANICAL side, from the hour angle.

        The rule is the AM5 simulator's `AxesModel.branch_for`, deliberately:
        `h < 0` is WEST and `h > 0` is EAST, so the two simulators agree and a
        survey written against one runs against the other. `h == 0` exactly is a
        coin flip on real hardware, so it reports the EAST branch rather than
        pretending to a precision it does not have.

        This was a bare cell that started UNKNOWN and never changed until
        2026-08, so a simulated meridian flip did not exist.
        """
        if self._pier_side_override is not None:
            return self._pier_side_override
        h = self._hour_angle_hours()
        if h is None:
            return TelescopePierSide.UNKNOWN
        return TelescopePierSide.WEST if h < 0.0 else TelescopePierSide.EAST

    def get_mount_side(self):
        """The GEOMETRIC pointing state -- Wallace's normal/beyond.

        A German equatorial reaches the same sky point two ways: `(-h, dec)`,
        or `(-h + 180, 180 - dec)` with the declination axis carried past the
        pole. The second has `|mechanical dec| > 90`, which is what BEYOND
        means, and Eqn 24 reverses `CH` and `NP` there.

        **Which mechanical side that is, is a property of the mount, and for a
        simulator it is a declared convention rather than a measurement.** This
        one declares WEST to be NORMAL and EAST to be BEYOND, so a survey
        crossing the meridian exercises both branches of
        `PointingModel::apply`. A real driver must derive this from its own
        encoder -- see `TelescopePierSide` -- and must not copy this line.
        """
        mechanical = self.get_pier_side()
        if mechanical == TelescopePierSide.WEST:
            return TelescopePierSide.NORMAL
        if mechanical == TelescopePierSide.EAST:
            return TelescopePierSide.BEYOND
        return TelescopePierSide.UNKNOWN

    def _hour_angle_hours(self):
        """LST - RA, wrapped to [-12, +12) hours, or None if the site cannot say."""
        try:
            lst_deg = self.get_site().lst_in_rads() * 180.0 / math.pi
        except Exception:
            return None
        return ((lst_deg - self._ra * 15.0) / 15.0 + 12.0) % 24.0 - 12.0
