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
        self._az = Coord.fromDMS(0)
        self._alt = Coord.fromDMS(70)

        self._slewing = False
        self._tracking = True
        self._parked = False

        self._abort = threading.Event()

        self._epoch = Epoch.J2000

        self._cover = False
        self._pierside = TelescopePierSide.UNKNOWN

        self._ra = Position.fromRaDec(0, 0).ra
        self._dec = Position.fromRaDec(0, 0).dec
        self._alt = Position.fromAltAz(0, 0).alt
        self._az = Position.fromAltAz(0, 0).az

    def _setAltAzFromRaDec(self):
        altAz = self._getSite().raDecToAltAz(Position.fromRaDec(self._ra, self._dec))
        self._alt = altAz.alt
        self._az = altAz.az

    def _getSite(self):
        # FIXME: create the proxy directly and cache it
        return self.getManager().getProxy("/Site/0")

    def _setRaDecFromAltAz(self):
        raDec = self._getSite().altAzToRaDec(Position.fromAltAz(self._alt, self._az))
        self._ra = raDec.ra
        self._dec = raDec.dec

    def _setAltAzFromRaDec(self):
        altAz = self._getSite().raDecToAltAz(Position.fromRaDec(self._ra, self._dec))
        self._alt = altAz.alt
        self._az = altAz.az

    def __start__(self):
        self.setHz(1)

    @lock
    def control(self):
        self._getSite()
        if not self._slewing:
            if self._tracking:
                self._setAltAzFromRaDec()
                try:
                    self._validateAltAz(self.getPositionAltAz())
                except ObjectTooLowException as msg:
                    self.log.exception(msg)
                    self._stopTracking()
                    self.trackingStopped(
                        self.getPositionRaDec(), TelescopeStatus.OBJECT_TOO_LOW
                    )
            else:
                self._setRaDecFromAltAz()
        return True

    def slewToRaDec(self, position):

        if not isinstance(position, Position):
            position = Position.fromRaDec(position[0], position[1], epoch=Epoch.J2000)

        self._validateRaDec(position)

        self.slewBegin(position)

        ra_steps = position.ra - self.getRa()
        ra_steps = float(ra_steps / 10.0)

        dec_steps = position.dec - self.getDec()
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
            self._setAltAzFromRaDec()

            time.sleep(0.5)
            t += 0.5

        self._slewing = False

        self.startTracking()

        self.slewComplete(self.getPositionRaDec(), status)

    @lock
    def slewToAltAz(self, position):

        if not isinstance(position, Position):
            position = Position.fromAltAz(*position)

        self._validateAltAz(position)

        self.slewBegin(self._getSite().altAzToRaDec(position))

        alt_steps = position.alt - self.getAlt()
        alt_steps = float(alt_steps / 10.0)

        az_steps = position.az - self.getAz()
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
            self._setRaDecFromAltAz()

            time.sleep(0.5)
            t += 0.5

        self._slewing = False

        self.slewComplete(self.getPositionRaDec(), status)

    def abortSlew(self):
        self._abort.set()
        while self.isSlewing():
            time.sleep(0.1)

        self._slewing = False

    def isSlewing(self):
        return self._slewing

    @lock
    def moveEast(self, offset, rate=SlewRate.MAX):

        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra + Coord.fromAS(offset), pos.dec)
        self.slewBegin(pos)

        self._ra += Coord.fromAS(offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveWest(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra + Coord.fromAS(-offset), pos.dec)
        self.slewBegin(pos)

        self._ra += Coord.fromAS(-offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveNorth(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra, pos.dec + Coord.fromAS(offset))
        self.slewBegin(pos)

        self._dec += Coord.fromAS(offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def moveSouth(self, offset, rate=SlewRate.MAX):
        self._slewing = True

        pos = self.getPositionRaDec()
        pos = Position.fromRaDec(pos.ra, pos.dec + Coord.fromAS(-offset))
        self.slewBegin(pos)

        self._dec += Coord.fromAS(-offset)
        self._setAltAzFromRaDec()

        self._slewing = False
        self.slewComplete(self.getPositionRaDec(), TelescopeStatus.OK)

    @lock
    def getRa(self):
        return self._ra

    @lock
    def getDec(self):
        return self._dec

    @lock
    def getAz(self):
        return self._az

    @lock
    def getAlt(self):
        return self._alt

    @lock
    def getPositionRaDec(self):
        return Position.fromRaDec(self.getRa(), self.getDec(), epoch=self._epoch)

    @lock
    def getPositionAltAz(self):
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def getTargetRaDec(self):
        return Position.fromRaDec(self.getRa(), self.getDec())

    @lock
    def getTargetAltAz(self):
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def syncRaDec(self, position):
        if not isinstance(position, Position):
            position = Position.fromRaDec(*position)

        self._ra = position.ra
        self._dec = position.dec

    @lock
    def park(self):
        self.log.info("Parking...")
        self._parked = True
        self.parkComplete()

    @lock
    def unpark(self):
        self.log.info("Unparking...")
        self._parked = False
        self.unparkComplete()

    def isParked(self):
        return self._parked

    @lock
    def startTracking(self):
        self._tracking = True
        self.trackingStarted(self.getPositionRaDec())

    @lock
    def stopTracking(self):
        self._stopTracking()
        self.trackingStopped(self.getPositionRaDec(), TelescopeStatus.ABORTED)

    def _stopTracking(self):
        self._tracking = False

    def isTracking(self):
        return self._tracking

    def openCover(self):
        self._cover = True

    def closeCover(self):
        self._cover = False

    def isCoverOpen(self):
        return self._cover

    def setPierSide(self, side):
        self._pierside = side

    def getPierSide(self):
        return self._pierside
