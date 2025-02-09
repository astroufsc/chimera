#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.cli import ChimeraCLI, action

from chimera.interfaces.filterwheel import InvalidFilterPositionException

import sys



class ChimeraFilter(ChimeraCLI):

    def __init__(self):
        ChimeraCLI.__init__(self, "chimera-filter", "Filter Wheel Controller", 0.1)

        self.addHelpGroup("INFO", "Filter Wheel Information")
        self.addHelpGroup("FILTER_CHANGE", "Filter Position")

        self.addHelpGroup("FILTER", "Filter Wheel configuration")
        self.addInstrument(
            name="wheel",
            cls="FilterWheel",
            required=True,
            help="Filter Wheel instrument to be used."
            "If blank, try to guess from chimera.config",
            helpGroup="FILTER",
        )

    @action(
        short="F",
        long="--list-filters",
        helpGroup="INFO",
        help="Print available filter names.",
    )
    def filters(self, options):

        self.out("Available filters:", end="")

        for i, f in enumerate(self.wheel.getFilters()):
            self.out(str(f), end="")

        self.out()
        self.exit()

    @action(help="Print Filter Wheel information and exit", helpGroup="INFO")
    def info(self, options):

        self.out("=" * 40)
        self.out(
            "Filter Wheel: %s (%s)" % (self.wheel.getLocation(), self.wheel["device"])
        )
        self.out("Current Filter:", self.wheel.getFilter())

        self.out("Available filters:", end="")
        for i, f in enumerate(self.wheel.getFilters()):
            self.out(str(f), end="")
        self.out()
        self.out("=" * 40)

    @action(
        long="--get-filter",
        help="Get the current filter name",
        helpGroup="FILTER_CHANGE",
        actionGroup="FILTER_CHANGE",
    )
    def getFilter(self, options):
        self.out("Current Filter:", self.wheel.getFilter())
        self.exit()

    @action(
        name="filtername",
        short="f",
        long="--set-filter",
        type="str",
        help="Set current filter.",
        actionGroup="FILTER_CHANGE",
        helpGroup="FILTER_CHANGE",
    )
    def changeFilter(self, options):

        if self.options.filtername not in self.wheel.getFilters():
            self.err("Invalid filter '%s'" % self.options.filtername)
            self.exit()

        self.out("Changing current filter to %s ..." % self.options.filtername, end="")
        try:
            self.wheel.setFilter(self.options.filtername)
            self.out("OK")
        except InvalidFilterPositionException:
            self.err("ERROR (Invalid Filter)")


def main():
    cli = ChimeraFilter()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":

    main()
