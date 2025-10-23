#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import copy
import sys

from chimera.core.exceptions import ObjectNotFoundException, print_exception
from chimera.core.version import _chimera_version_
from chimera.interfaces.rotator import RotatorStatus
from chimera.util.coord import Coord
from chimera.util.output import green, red, yellow

from .cli import ChimeraCLI, action


class ChimeraRotator(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-rotator", "Rotator controller", _chimera_version_
        )

        self.add_help_group("ROTATOR", "Rotator")
        self.add_instrument(
            name="rotator",
            cls="Rotator",
            required=True,
            help="Rotator instrument to be used",
            help_group="ROTATOR",
        )

        self.add_help_group("COMMANDS", "Commands")

    @action(
        long="to",
        type="float",
        help="Move rotator to ANGLE position (in degrees)",
        metavar="ANGLE",
        help_group="COMMANDS",
    )
    def move_to(self, options):
        self.out("Moving rotator to %.2f degrees ... " % options.move_to, end="")
        self.rotator.move_to(options.move_to)
        self.out("OK")

    @action(
        long="by",
        type="float",
        help="Move rotator by relative ANGLE (in degrees)",
        metavar="ANGLE",
        help_group="COMMANDS",
    )
    def move_by(self, options):
        self.out("Moving rotator by %.2f degrees ... " % options.move_by, end="")
        self.rotator.move_by(options.move_by)
        self.out("OK")

    @action(help="Print rotator information", help_group="COMMANDS")
    def info(self, options):
        self.out("=" * 40)
        self.out(
            "Rotator: %s (%s)." % (self.rotator.get_location(), self.rotator["device"])
        )
        self.out(
            "Current rotator position: %.2f degrees." % self.rotator.get_position()
        )
        if hasattr(self.rotator, "get_model") and self.rotator["rotator_model"]:
            self.out("Rotator model: %s." % self.rotator["rotator_model"])
        self.out("=" * 40)

    def __abort__(self):
        self.out("\naborting... ", end="")

        # copy self.rotator Proxy because we are running from a different thread
        if hasattr(self, "rotator"):
            rotator = copy.copy(self.rotator)
            rotator.abort_move()


def main():
    cli = ChimeraRotator()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
