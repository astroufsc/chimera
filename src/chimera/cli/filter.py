#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import sys

from chimera.core.version import _chimera_version_
from chimera.interfaces.filterwheel import InvalidFilterPositionException

from .cli import ChimeraCLI, action


class ChimeraFilter(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-filter", "Filter Wheel Controller", _chimera_version_
        )

        self.add_help_group("INFO", "Filter Wheel Information")
        self.add_help_group("FILTER_CHANGE", "Filter Position")

        self.add_help_group("FILTER", "Filter Wheel configuration")
        self.add_instrument(
            name="wheel",
            cls="FilterWheel",
            required=True,
            help="Filter Wheel instrument to be used."
            "If blank, try to guess from chimera.config",
            help_group="FILTER",
        )

    @action(
        short="F",
        long="--list-filters",
        help_group="INFO",
        help="Print available filter names.",
    )
    def filters(self, options):
        self.out("Available filters:", end="")

        for i, f in enumerate(self.wheel.get_filters()):
            self.out(str(f), end="")

        self.out()
        self.exit()

    @action(help="Print Filter Wheel information and exit", help_group="INFO")
    def info(self, options):
        self.out("=" * 40)
        self.out(
            "Filter Wheel: %s (%s)" % (self.wheel.get_location(), self.wheel["device"])
        )
        self.out("Current Filter:", self.wheel.get_filter())

        self.out("Available filters:", end="")
        for i, f in enumerate(self.wheel.get_filters()):
            self.out(str(f), end="")
        self.out()
        self.out("=" * 40)

    @action(
        long="--get-filter",
        help="Get the current filter name",
        help_group="FILTER_CHANGE",
        action_group="FILTER_CHANGE",
    )
    def get_filter(self, options):
        self.out("Current Filter:", self.wheel.get_filter())
        self.exit()

    @action(
        name="filtername",
        short="f",
        long="--set-filter",
        type="str",
        help="Set current filter.",
        action_group="FILTER_CHANGE",
        help_group="FILTER_CHANGE",
    )
    def change_filter(self, options):
        if self.options.filtername not in self.wheel.get_filters():
            self.err("Invalid filter '%s'" % self.options.filtername)
            self.exit()

        self.out("Changing current filter to %s ..." % self.options.filtername, end="")
        try:
            self.wheel.set_filter(self.options.filtername)
            self.out("OK")
        except InvalidFilterPositionException:
            self.err("ERROR (Invalid Filter)")


def main():
    cli = ChimeraFilter()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
