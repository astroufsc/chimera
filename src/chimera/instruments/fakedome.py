# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.lock import lock
from chimera.util.coord import Coord

from chimera.interfaces.dome import InvalidDomePositionException, DomeStatus
from chimera.instruments.dome import DomeBase

import time
import threading


class FakeDome(DomeBase):

    def __init__(self):
        DomeBase.__init__(self)

        self._position = 0
        self._slewing = False
        self._slitOpen = False
        self._flapOpen = False
        self._abort = threading.Event()
        self._maxSlewTime = 5 / 180.0

    def __start__(self):
        self.setHz(1.0 / 30.0)

    @lock
    def slewToAz(self, az):

        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if az > 360:
            raise InvalidDomePositionException(
                f"Cannot slew to {az}. " "Outside azimuth limits."
            )

        self._abort.clear()
        self._slewing = True

        self.slewBegin(az)
        self.log.info(f"Slewing to {az}")

        # slew time ~ distance from current position
        distance = abs(float(az - self._position))
        if distance > 180:
            distance = 360 - distance

        self.log.info(f"Slew distance {distance:.3f} deg")

        slew_time = distance * self._maxSlewTime

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
            self._position = self.position + distance / 2.0

        self._slewing = False
        self.slewComplete(self.getAz(), status)

    def isSlewing(self):
        return self._slewing

    def abortSlew(self):
        if not self.isSlewing():
            return

        self._abort.set()
        while self.isSlewing():
            time.sleep(0.1)

    @lock
    def getAz(self):
        return Coord.fromD(self._position)

    @lock
    def openSlit(self):
        self.log.info("Opening slit")
        time.sleep(2)
        self._slitOpen = True
        self.slitOpened(self.getAz())

    @lock
    def closeSlit(self):
        self.log.info("Closing slit")
        if self.isFlapOpen():
            self.log.warning("Dome flap open. Closing it before closing the slit.")
            self.closeFlap()
        time.sleep(2)
        self._slitOpen = False
        self.slitClosed(self.getAz())

    def isSlitOpen(self):
        return self._slitOpen

    @lock
    def openFlap(self):
        self.log.info("Opening flap")
        if not self.isSlitOpen():
            raise InvalidDomePositionException(
                "Cannot open dome flap with slit closed."
            )
        time.sleep(2)
        self._flapOpen = True
        self.flapOpened(self.getAz())

    @lock
    def closeFlap(self):
        self.log.info("Closing flap")
        time.sleep(2)
        self._slitOpen = False
        self.slitClosed(self.getAz())

    def isFlapOpen(self):
        return self._flapOpen
