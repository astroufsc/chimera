# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
# SPDX-FileCopyrightText: 2006-present Antonio Kanaan <kanaan@astro.ufsc.br>

import queue
import threading
import functools

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.dome import Mode, DomeSlew, DomeSlit, DomeFlap, DomeSync
from chimera.core.lock import lock
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.exceptions import ChimeraException
from chimera.util.coord import Coord
from chimera.core.site import Site
from chimera.core.proxy import Proxy


__all__ = ["DomeBase"]


class DomeBase(ChimeraObject, DomeSlew, DomeSlit, DomeFlap, DomeSync):
    def __init__(self):
        ChimeraObject.__init__(self)

        self.queue = queue.Queue()
        self._mode = None

        # to reuse telescope proxy on control method
        self._telescope = None
        self._telescope_changed = False

        # to cache for az_resolution of the dome
        self.control_az_res = None

        self._wait_after_slew = threading.Event()
        self._wait_after_slew.clear()

    def __start__(self):

        self.set_hz(1 / 4.0)

        telescope = self.get_telescope()
        if telescope:
            self._connect_telescope_events()
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

        self.log.debug(f"Dome started in {self.get_mode()} mode.")

        return True

    def __stop__(self):

        if self["park_on_shutdown"]:
            try:
                self.stand()
                self.log.info("Parking the dome...")
                self.slew_to_az(self["park_position"])
            except Exception as e:
                self.log.warning("Unable to park dome: %s", str(e))

        if self["close_on_shutdown"] and self.is_slit_open():
            try:
                self.log.info("Closing the slit...")
                self.close_slit()
            except Exception as e:
                self.log.warning("Unable to close dome: %s", str(e))

        # telescope events
        self._disconnect_telescope_events()
        return True

    def _connect_telescope_events(self):

        telescope = self.get_telescope()
        if not telescope:
            self.log.warning(
                "Couldn't find telescope. Telescope events would"
                " not be monitored. Dome will stay in Stand mode."
            )
            self["mode"] == Mode.Stand
            return False

        telescope.slew_begin += self.get_proxy()._telescope_slew_begin_callback
        telescope.slew_complete += self.get_proxy()._telescope_slew_complete_callback
        return True

    def _disconnect_telescope_events(self):

        telescope = self.get_telescope()
        if telescope:
            telescope.slew_begin -= self.get_proxy()._telescope_slew_begin_callback
            telescope.slew_complete -= (
                self.get_proxy()._telescope_slew_complete_callback
            )
            return True
        return False

    def _reconnect_telescope_events(self):
        self._disconnect_telescope_events()
        self._connect_telescope_events()

    # telescope callbacks
    def _telescope_slew_begin_callback(self, target):
        self.log.debug(f"[event] telescope slewing to {target}.")

    def _telescope_slew_complete_callback(self, target, status):
        self.log.debug(
            f"[event] telescope slew complete, position={target} status={status}."
        )

    # utilities
    def get_telescope(self):
        try:
            proxy = self.get_proxy(self["telescope"])
            if not proxy.ping():
                return False
            else:
                return proxy
        except ObjectNotFoundException:
            return False

    def control(self):

        if self.get_mode() == Mode.Stand:
            return True

        if not self.queue.empty():
            self._process_queue()
            return True

        try:
            if not self._telescope or self._telescope_changed:
                self._telescope = self.get_telescope()
                self._telescope_changed = False
                if not self._telescope:
                    return True

            if self._telescope.is_slewing():
                self.log.debug("[control] telescope slewing... not checking az.")
                self._wait_after_slew.set()
                return True

            self._telescope_changed_position(self._telescope.get_az())
            # flag all waiting threads that the control loop already checked the new telescope position
            # probably adding new azimuth to the queue
            self._wait_after_slew.clear()

        except ObjectNotFoundException:
            raise ChimeraException(
                "Couldn't find the selected telescope." " Dome cannot track."
            )

        return True

    def _telescope_changed_position(self, az):

        if not isinstance(az, Coord):
            az = Coord.from_dms(az)

        if self._need_to_move(az):
            self.log.debug(
                f"[control] adding {az} to the queue (delta={abs(self.get_az() - az)})"
            )
            self.queue.put(az)
        else:
            self.log.debug(
                "[control] standing"
                f" (dome az={self.get_az()}, telescope az={az}, delta={abs(self.get_az() - az)}.)"
            )

    def _need_to_move(self, az):
        return abs(az - self.get_az()) >= self["az_resolution"]

    def _process_queue(self):

        if self._wait_after_slew.is_set():
            self._telescope_changed_position(self._telescope.get_az())

        if self.queue.empty():
            return

        self.log.debug(f"[control] processing queue... {self.queue.qsize()} item(s).")

        while not self.queue.empty():

            target = self.queue.get()
            try:
                self.log.debug(f"[queue] slewing to {target}")
                self.slew_to_az(target)
            finally:
                self.log.debug(f"[queue] slew to {target} complete")
                self.queue.task_done()

    @lock
    def track(self):
        if self.get_mode() == Mode.Track:
            return

        telescope = self.get_telescope()

        if telescope:
            self._reconnect_telescope_events()
            self._telescope_changed = True
            self.log.debug("[mode] tracking...")
            self._telescope_changed_position(telescope.get_az())
            self._mode = Mode.Track
            self._process_queue()
        else:
            self.log.warning(
                "Could not contact the given telescope, staying in Stand mode."
            )

    @lock
    def stand(self):
        self._process_queue()
        self.log.debug("[mode] standing...")
        self._mode = Mode.Stand

    @lock
    def sync_with_telescope(self):
        self.sync_begin()

        if self.get_mode() != Mode.Stand:
            self._telescope_changed_position(self._telescope.get_az())
            self._process_queue()

        self.sync_complete()

    @lock
    def is_sync_with_telescope(self):
        return self._need_to_move(self._telescope.get_az())

    def get_mode(self):
        return self._mode

    @lock
    def slew_to_az(self, az):
        raise NotImplementedError()

    def is_slewing(self):
        raise NotImplementedError()

    def abort_slew(self):
        raise NotImplementedError()

    @lock
    def get_az(self):
        raise NotImplementedError()

    @lock
    def open_slit(self):
        raise NotImplementedError()

    @lock
    def close_slit(self):
        raise NotImplementedError()

    def is_slit_open(self):
        raise NotImplementedError()

    @lock
    def open_flap(self):
        raise NotImplementedError()

    @lock
    def close_flap(self):
        raise NotImplementedError()

    def is_flap_open(self):
        raise NotImplementedError()

    def get_metadata(self, request):
        # Check first if there is metadata from a metadata override method.
        metadata = self.get_metadata_override(request)
        if metadata is not None:
            return metadata
        # If not, just go on with the instrument's default metadata.
        if self.is_slit_open():
            slit = "Open"
        else:
            slit = "Closed"

        return [
            ("DOME_MDL", str(self["model"]), "Dome Model"),
            ("DOME_TYP", str(self["style"]), "Dome Type"),
            ("DOME_TRK", str(self["mode"]), "Dome Tracking/Standing"),
            ("DOME_SLT", str(slit), "Dome slit status"),
        ]
