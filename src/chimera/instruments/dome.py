# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
# SPDX-FileCopyrightText: 2006-present Antonio Kanaan <kanaan@astro.ufsc.br>

import functools
import queue
import threading
from typing import cast

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.interfaces.dome import DomeFlap, DomeSlew, DomeSlit, DomeSync, Mode
from chimera.interfaces.telescope import Telescope

__all__ = ["DomeBase"]


class DomeBase(ChimeraObject, DomeSlew, DomeSlit, DomeFlap, DomeSync):
    def __init__(self):
        ChimeraObject.__init__(self)

        self.queue: queue.Queue[float] = queue.Queue()
        self._mode = Mode.Stand

        # to reuse telescope proxy on control method
        self._telescope = None
        self._telescope_changed = False

        # to cache for az_resolution of the dome
        self.control_az_res = None

        self._telescope_is_slewing = threading.Event()
        self._telescope_is_slewing.clear()

    def __start__(self):
        self.set_hz(1 / 4.0)

        if self["mode"] == Mode.Track:
            self.track()
        elif self["mode"] == Mode.Stand:
            self.stand()
        else:
            self.log.warning("Invalid dome mode: %s. Will use Stand mode instead.")
            self.stand()

        self.log.debug(f"Dome started in {self.get_mode()} mode.")

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

    def control(self) -> bool:
        if self.get_mode() == Mode.Stand:
            return True

        if not self.queue.empty():
            self._process_queue()
            return True

        if self.telescope.is_slewing():
            self.log.debug("[control] telescope is slewing. will wait until done")
            self._telescope_is_slewing.set()
            return True

        self._move_if_needed(self._get_telescope_az())

        # flag all waiting threads that the control loop already checked the new telescope position
        # probably adding new azimuth to the queue
        self._telescope_is_slewing.clear()

        return True

    @property
    @functools.cache
    def telescope(self) -> Telescope:
        return cast(Telescope, self.get_proxy(self["telescope"]))

    def _get_telescope_az(self) -> float:
        if not self.telescope.ping():
            self.log.warning(
                f"Could not contact {self['telescope']}, changin to Stand mode."
            )
            self.stand()
            return self.get_az()

        return self.telescope.get_az()

    def _move_if_needed(self, az: float):
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

    def _need_to_move(self, az: float) -> bool:
        return abs(az - self.get_az()) >= self["az_resolution"]

    def _process_queue(self):
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

        self.log.debug("[mode] tracking...")
        self._move_if_needed(self._get_telescope_az())
        self._mode = Mode.Track
        self._process_queue()

    @lock
    def stand(self):
        self._process_queue()
        self.log.debug("[mode] standing...")
        self._mode = Mode.Stand

    @lock
    def sync_with_telescope(self):
        self.sync_begin()

        if self.get_mode() != Mode.Stand:
            self._move_if_needed(self._get_telescope_az())
            self._process_queue()

        self.sync_complete()

    @lock
    def is_sync_with_telescope(self):
        return self._need_to_move(self._get_telescope_az())

    def get_mode(self):
        return self._mode

    @lock
    def slew_to_az(self, az: float) -> None:
        raise NotImplementedError()

    def is_slewing(self) -> bool:
        raise NotImplementedError()

    def abort_slew(self) -> None:
        raise NotImplementedError()

    @lock
    def get_az(self) -> float:
        raise NotImplementedError()

    @lock
    def open_slit(self) -> None:
        raise NotImplementedError()

    @lock
    def close_slit(self) -> None:
        raise NotImplementedError()

    def is_slit_open(self) -> bool:
        raise NotImplementedError()

    @lock
    def open_flap(self) -> None:
        raise NotImplementedError()

    @lock
    def close_flap(self) -> None:
        raise NotImplementedError()

    def is_flap_open(self) -> bool:
        raise NotImplementedError()

    def get_metadata(self, request) -> list[tuple[str, str, str]]:
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
