#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import sys
import threading

from chimera.core.version import chimera_version
from chimera.interfaces.autoguider import GuiderStatus

from .cli import ChimeraCLI, ParameterType, action


class ChimeraGuide(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-guider", "Autoguider controller", chimera_version
        )

        self.add_help_group("GUIDER", "Autoguider")
        self.add_instrument(
            name="guider",
            cls="Autoguider",
            required=True,
            help_group="GUIDER",
            help="Autoguider instrument to be used",
        )

        self.add_parameters(
            dict(
                name="recalibrate",
                long="recalibrate",
                type=ParameterType.BOOLEAN,
                help_group="GUIDER",
                help="Discard the current calibration and recalibrate before guiding.",
                default=False,
            ),
            dict(
                name="nowait",
                long="nowait",
                type=ParameterType.BOOLEAN,
                help_group="GUIDER",
                help="Don't wait for the guider to settle, return immediately.",
                default=False,
            ),
            dict(
                name="ra_only",
                long="ra-only",
                type=ParameterType.BOOLEAN,
                help_group="GUIDER",
                help="Dither only in right ascension.",
                default=False,
            ),
        )

        self.add_help_group("COMMANDS", "Commands")

    @action(help="Start guiding", help_group="COMMANDS")
    def start(self, options):
        settled = threading.Event()

        def star_acquired(position):
            self.out(f"Guide star acquired at {position}.")

        def guide_start(position):
            self.out(f"Guiding started at {position}, waiting to settle ...")
            settled.set()

        self.guider.star_acquired += star_acquired
        self.guider.guide_start += guide_start

        self.out("Starting autoguider ... ", end="")
        try:
            self.guider.start_guiding(options.recalibrate, not options.nowait)
            self.out("OK")
        except Exception as e:
            self.exit(f"ERROR ({e})")

        if not options.nowait and not settled.is_set():
            # settled before the event subscription was in place
            self.out("Guiding started and settled.")

    @action(help="Stop guiding", help_group="COMMANDS")
    def stop(self, options):
        self.out("Stopping autoguider ... ", end="")
        self.guider.stop_guiding()
        self.out("OK")

    @action(help="Abort guiding as soon as possible", help_group="COMMANDS")
    def abort(self, options):
        self.out("Aborting autoguider ... ", end="")
        self.guider.abort()
        self.out("OK")

    @action(
        long="dither",
        type="float",
        help="Dither the guide star position by up to AMOUNT pixels",
        metavar="AMOUNT",
        help_group="COMMANDS",
    )
    def dither(self, options):
        self.out(f"Dithering by up to {options.dither} pixels ... ", end="")
        try:
            self.guider.dither(options.dither, options.ra_only, not options.nowait)
            self.out("OK")
        except Exception as e:
            self.exit(f"ERROR ({e})")

    @action(
        long="find-star",
        help="Find a guide star in the current field of view",
        help_group="COMMANDS",
    )
    def find_star(self, options):
        self.out("Looking for a guide star ... ", end="")
        try:
            position = self.guider.find_star()
            self.out(f"OK (found at {position})")
        except Exception as e:
            self.exit(f"ERROR ({e})")

    @action(
        long="monitor",
        help="Print guider offsets until interrupted (Ctrl-C)",
        help_group="COMMANDS",
    )
    def monitor(self, options):
        stopped = threading.Event()

        def offset_complete(offset):
            self.out(
                "#%05d dx: %8.3f dy: %8.3f ra: %8.3f dec: %8.3f snr: %6.2f"
                % (
                    offset.get("frame") or 0,
                    offset.get("dx") or 0.0,
                    offset.get("dy") or 0.0,
                    offset.get("ra_distance") or 0.0,
                    offset.get("dec_distance") or 0.0,
                    offset.get("snr") or 0.0,
                )
            )

        def star_lost():
            self.out("Guide star lost!")

        def guide_stop(state, msg=None):
            self.out(f"Guiding stopped ({state}).")
            stopped.set()

        self.guider.offset_complete += offset_complete
        self.guider.star_lost += star_lost
        self.guider.guide_stop += guide_stop

        self.out("Monitoring guider (Ctrl-C to quit) ...")
        try:
            stopped.wait()
        except KeyboardInterrupt:
            pass

    @action(short="i", help="Print guider current information", help_group="COMMANDS")
    def info(self, options):
        self.out("=" * 40)
        self.out(f"Autoguider: {self.guider.get_location()}")
        status = self.guider.get_status()
        self.out(f"Status: {status}")
        self.out(f"Guiding: {self.guider.is_guiding()}")
        if status == GuiderStatus.ERROR:
            self.out("(guider in error state or not connected)")
        self.out("=" * 40)


def main():
    cli = ChimeraGuide()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
