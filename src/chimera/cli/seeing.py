#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime
import sys

from chimera.core.version import _chimera_version_
from chimera.util.output import green, red

from .cli import ChimeraCLI, action


class ChimeraSeeing(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-seeing", "Seeing Monitor script", _chimera_version_
        )

        self.addHelpGroup("SM", "Seeing Monitor")
        self.addHelpGroup("COMMANDS", "Commands")

        self.addInstrument(
            name="seeingmonitor",
            cls="SeeingMonitor",
            required=True,
            helpGroup="WS",
            help="Seeing Monitor to be used",
        )

        self.addParameters(
            dict(
                name="max_mins",
                short="t",
                type="float",
                default=10,
                helpGroup="COMMANDS",
                help="Mark in red date/time values if older than this time in minutes",
            )
        )

    @action(
        short="i", help="Print seeing monitor current information", helpGroup="COMMANDS"
    )
    def info(self, options):
        self.out("=" * 80)
        self.out(
            "Seeing Monitor: %s %s (%s)"
            % (
                self.seeingmonitor.getLocation(),
                self.seeingmonitor["model"],
                self.seeingmonitor["device"],
            )
        )
        self.out("=" * 80)

        for attr in ("seeing", "seeing_at_zenith", "airmass", "flux"):
            try:
                v = self.seeingmonitor.__getattr__(attr)()
                if isinstance(v, NotImplementedError) or not v:
                    continue
                t = (
                    red(v.time.__str__())
                    if datetime.datetime.utcnow() - v.time
                    > datetime.timedelta(minutes=self.options.max_mins)
                    else green(v.time.__str__())
                )
                self.out(
                    t
                    + "  "
                    + attr.replace("_", " ")
                    + ": {0.value:.2f} {0.unit:s} ".format(v)
                )
            except NotImplementedError:
                pass

        self.out("=" * 80)

        return


def main():
    cli = ChimeraSeeing()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
