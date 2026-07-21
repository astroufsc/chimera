# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
"""Fake autoguider that pretends to guide, for testing and simulations.

It keeps no hardware connection: star acquisition always succeeds at a
fixed position and guiding/dithering settle instantly. While guiding it
publishes offset_complete telemetry so consumers of that event, such as
chimera-guide --monitor, can be exercised without hardware.
"""

import random

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.interfaces.autoguider import (
    Autoguider,
    GuiderException,
    GuiderStatus,
)


class FakeAutoguider(ChimeraObject, Autoguider):
    __config__ = {
        "freq": 1.0,  # simulated correction rate (Hz)
        "scatter": 0.4,  # rms of the simulated guide error (pixels)
        "pixel_scale": 0.5,  # arcsec/pixel, for the ra/dec distance fields
    }

    def __init__(self):
        ChimeraObject.__init__(self)
        self._status = GuiderStatus.OFF
        self._lock_position = [512.0, 512.0]  # fake guide star position (pixels)
        self._frame = 0

    # Autoguider interface

    @lock
    def start_guiding(self, recalibrate=False, wait=False):
        position = self.find_star()
        self._status = GuiderStatus.GUIDING
        self.guide_start(position)
        return position

    def stop_guiding(self):
        self._stop(GuiderStatus.OFF)

    def abort(self):
        self._stop(GuiderStatus.ABORTED)

    def is_guiding(self):
        return self._status == GuiderStatus.GUIDING

    def get_status(self):
        return self._status

    @lock
    def dither(self, amount=None, ra_only=None, wait=False):
        if not self.is_guiding():
            raise GuiderException("Cannot dither: not guiding.")

        amount = float(self["dither_amount"] if amount is None else amount)
        ra_only = bool(self["dither_ra_only"] if ra_only is None else ra_only)

        dx = amount
        dy = 0.0 if ra_only else amount
        self._lock_position = [self._lock_position[0] + dx, self._lock_position[1] + dy]
        self.dither_complete([dx, dy], GuiderStatus.OK)

    @lock
    def find_star(self):
        self.star_acquired(self._lock_position)
        return self._lock_position

    # simulated telemetry

    def control(self):
        if self.is_guiding():
            self._frame += 1
            scatter = float(self["scatter"])
            dx = random.gauss(0.0, scatter)
            dy = random.gauss(0.0, scatter)
            scale = float(self["pixel_scale"])
            self.offset_complete(
                {
                    "frame": self._frame,
                    "dx": dx,
                    "dy": dy,
                    "ra_distance": dx * scale,
                    "dec_distance": dy * scale,
                    "snr": random.uniform(20.0, 60.0),
                }
            )
        return True

    # internals

    def _stop(self, status):
        was_guiding = self.is_guiding()
        self._status = status
        if was_guiding:
            self.guide_stop(status)
