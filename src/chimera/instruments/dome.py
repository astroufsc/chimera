# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
# SPDX-FileCopyrightText: 2006-present Antonio Kanaan <kanaan@astro.ufsc.br>

import queue
import threading

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.dome import Mode, DomeSlew, DomeSlit, DomeFlap, DomeSync
from chimera.core.lock import lock
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.exceptions import ChimeraException
from chimera.util.coord import Coord


__all__ = ["DomeBase"]


class DomeBase(ChimeraObject, DomeSlew, DomeSlit, DomeFlap, DomeSync):
    def __init__(self):
        ChimeraObject.__init__(self)

        self.queue = queue.Queue()
        self._mode = None

        # to reuse telescope proxy on control method
        self._tel = None
        self._telChanged = False

        # to cache for az_resolution of the dome
        self.controlAzRes = None

        self._waitAfterSlew = threading.Event()
        self._waitAfterSlew.clear()

    def __start__(self):

        self.setHz(1 / 4.0)

        tel = self.getTelescope()
        if tel:
            self._connectTelEvents()
        else:
            self.log.warning(
                "Couldn't find telescope. Telescope events would"
                " not be monitored. Dome will stay in Stand mode."
            )
            self["mode"] = Mode.Stand

        if self["mode"] == Mode.Track:
            self.track()
        elif self["mode"] == Mode.Stand:
            self.stand()
        else:
            self.log.warning("Invalid dome mode: %s. " "Will use Stand mode instead.")
            self.stand()

        self.log.debug(f"Dome started in {self.getMode()} mode.")

        return True

    def __stop__(self):

        if self["park_on_shutdown"]:
            try:
                self.stand()
                self.log.info("Parking the dome...")
                self.slewToAz(self["park_position"])
            except Exception as e:
                self.log.warning("Unable to park dome: %s", str(e))

        if self["close_on_shutdown"] and self.isSlitOpen():
            try:
                self.log.info("Closing the slit...")
                self.closeSlit()
            except Exception as e:
                self.log.warning("Unable to close dome: %s", str(e))

        # telescope events
        self._disconnectTelEvents()
        return True

    def _connectTelEvents(self):

        tel = self.getTelescope()
        if not tel:
            self.log.warning(
                "Couldn't find telescope. Telescope events would"
                " not be monitored. Dome will stay in Stand mode."
            )
            self["mode"] == Mode.Stand
            return False

        tel.slewBegin += self.getProxy()._telSlewBeginClbk
        tel.slewComplete += self.getProxy()._telSlewCompleteClbk
        return True

    def _disconnectTelEvents(self):

        tel = self.getTelescope()
        if tel:
            tel.slewBegin -= self.getProxy()._telSlewBeginClbk
            tel.slewComplete -= self.getProxy()._telSlewCompleteClbk
            return True
        return False

    def _reconnectTelEvents(self):
        self._disconnectTelEvents()
        self._connectTelEvents()

    # telescope callbacks
    def _telSlewBeginClbk(self, target):
        self.log.debug(f"[event] telescope slewing to {target}.")

    def _telSlewCompleteClbk(self, target, status):
        self.log.debug(
            f"[event] telescope slew complete, position={target} status={status}."
        )

    # utilitaries
    def getTelescope(self):
        try:
            p = self.getManager().getProxy(self["telescope"])
            if not p.ping():
                return False
            else:
                return p
        except ObjectNotFoundException:
            return False

    def control(self):

        if self.getMode() == Mode.Stand:
            return True

        if not self.queue.empty():
            self._processQueue()
            return True

        try:
            if not self._tel or self._telChanged:
                self._tel = self.getTelescope()
                self._telChanged = False
                if not self._tel:
                    return True

            if self._tel.isSlewing():
                self.log.debug("[control] telescope slewing... not checking az.")
                self._waitAfterSlew.set()
                return True

            self._telescopeChanged(self._tel.getAz())
            # flag all waiting threads that the control loop already checked the new telescope position
            # probably adding new azimuth to the queue
            self._waitAfterSlew.clear()

        except ObjectNotFoundException:
            raise ChimeraException(
                "Couldn't found the selected telescope." " Dome cannnot track."
            )

        return True

    def _telescopeChanged(self, az):

        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if self._needToMove(az):
            self.log.debug(
                f"[control] adding {az} to the queue (delta={abs(self.getAz() - az)})"
            )
            self.queue.put(az)
        else:
            self.log.debug(
                "[control] standing"
                f" (dome az={self.getAz()}, tel az={az}, delta={abs(self.getAz() - az)}.)"
            )

    def _needToMove(self, az):
        return abs(az - self.getAz()) >= self["az_resolution"]

    def _processQueue(self):

        if self._waitAfterSlew.is_set():
            self._telescopeChanged(self._tel.getAz())

        if self.queue.empty():
            return

        self.log.debug(f"[control] processing queue... {self.queue.qsize()} item(s).")

        while not self.queue.empty():

            target = self.queue.get()
            try:
                self.log.debug(f"[queue] slewing to {target}")
                self.slewToAz(target)
            finally:
                self.log.debug(f"[queue] slew to {target} complete")
                self.queue.task_done()

    @lock
    def track(self):
        if self.getMode() == Mode.Track:
            return

        tel = self.getTelescope()

        if tel:
            self._reconnectTelEvents()
            self._telChanged = True
            self.log.debug("[mode] tracking...")
            self._telescopeChanged(tel.getAz())
            self._mode = Mode.Track
        else:
            self.log.warning(
                "Could not contact the given telescope, staying in Stand mode."
            )

    @lock
    def stand(self):
        self._processQueue()
        self.log.debug("[mode] standing...")
        self._mode = Mode.Stand

    @lock
    def syncWithTel(self):
        self.syncBegin()

        if self.getMode() != Mode.Stand:
            self._telescopeChanged(self._tel.getAz())
            self._processQueue()

        self.syncComplete()

    @lock
    def isSyncWithTel(self):
        return self._needToMove(self._tel.getAz())

    def getMode(self):
        return self._mode

    @lock
    def slewToAz(self, az):
        raise NotImplementedError()

    def isSlewing(self):
        raise NotImplementedError()

    def abortSlew(self):
        raise NotImplementedError()

    @lock
    def getAz(self):
        raise NotImplementedError()

    @lock
    def openSlit(self):
        raise NotImplementedError()

    @lock
    def closeSlit(self):
        raise NotImplementedError()

    def isSlitOpen(self):
        raise NotImplementedError()

    @lock
    def openFlap(self):
        raise NotImplementedError()

    @lock
    def closeFlap(self):
        raise NotImplementedError()

    def isFlapOpen(self):
        raise NotImplementedError()

    def getMetadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.getMetadataOverride(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        if self.isSlitOpen():
            slit = "Open"
        else:
            slit = "Closed"

        return [
            ("DOME_MDL", str(self["model"]), "Dome Model"),
            ("DOME_TYP", str(self["style"]), "Dome Type"),
            ("DOME_TRK", str(self["mode"]), "Dome Tracking/Standing"),
            ("DOME_SLT", str(slit), "Dome slit status"),
        ]
