# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import threading
import time

from chimera.core.lock import lock
from chimera.instruments.dome import DomeBase
from chimera.interfaces.dome import DomeStatus, InvalidDomePositionException


class FakeDome(DomeBase):
    def __init__(self):
        DomeBase.__init__(self)

        self._position: float = 0.0
        self._slewing = False
        self._slit_open = False
        self._flap_open = False
        self._abort = threading.Event()
        self._max_slew_time = 5 / 180.0

    def __start__(self):
        self.set_hz(1.0 / 30.0)

    @lock
    def slew_to_az(self, az: float):
        if az > 360:
            raise InvalidDomePositionException(
                f"Cannot slew to {az}. Outside azimuth limits."
            )

        self._abort.clear()
        self._slewing = True

        self.slew_begin(az)
        self.log.info(f"Slewing to {az}")

        # slew time ~ distance from current position
        distance = abs(float(az - self._position))
        if distance > 180:
            distance = 360 - distance

        self.log.info(f"Slew distance {distance:.3f} deg")

        slew_time = distance * self._max_slew_time

        self.log.info(f"Slew time ~ {slew_time:.3f} s")

        status = DomeStatus.OK

        t = 0
        while t < slew_time:
            if self._abort.is_set():
                self._slewing = False
                status = DomeStatus.ABORTED
                break

            time.sleep(0.1)
            t += 0.1

        if status == DomeStatus.OK:
            self._position = az  # move :)
        else:
            # assume half movement in case of abort
            self._position += distance / 2.0

        self._slewing = False
        self.slew_complete(self.get_az(), status)

    def is_slewing(self) -> bool:
        return self._slewing

    def abort_slew(self):
        if not self.is_slewing():
            return

        self._abort.set()
        while self.is_slewing():
            time.sleep(0.1)

    @lock
    def get_az(self) -> float:
        return self._position

    @lock
    def open_slit(self):
        self.log.info("Opening slit")
        time.sleep(2)
        self._slit_open = True
        self.slit_opened(self.get_az())

    @lock
    def close_slit(self):
        self.log.info("Closing slit")
        if self.is_flap_open():
            self.log.warning("Dome flap open. Closing it before closing the slit.")
            self.close_flap()
        time.sleep(2)
        self._slit_open = False
        self.slit_closed(self.get_az())

    def is_slit_open(self):
        return self._slit_open

    @lock
    def open_flap(self):
        self.log.info("Opening flap")
        if not self.is_slit_open():
            raise InvalidDomePositionException(
                "Cannot open dome flap with slit closed."
            )
        time.sleep(2)
        self._flap_open = True
        self.flap_opened(self.get_az())

    @lock
    def close_flap(self):
        self.log.info("Closing flap")
        time.sleep(2)
        self._slit_open = False
        self.slit_closed(self.get_az())

    def is_flap_open(self):
        return self._flap_open
