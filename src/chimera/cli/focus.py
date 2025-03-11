#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import os
import re
import sys
import time

from chimera.core.version import _chimera_version_
from chimera.interfaces.autofocus import FocusNotFoundException, StarNotFoundException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.interfaces.focuser import (
    ControllableAxis,
    FocuserAxis,
    FocuserFeature,
    InvalidFocusPositionException,
)
from chimera.util.ds9 import DS9
from chimera.util.sextractor import SExtractorException

from .cli import ChimeraCLI, ParameterType, action, parameter


class ChimeraFocus(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-focus", "Focuser controller", _chimera_version_
        )

        self.addHelpGroup("FOCUS", "Focus")
        self.addInstrument(
            name="focuser",
            cls="Focuser",
            required=True,
            helpGroup="FOCUS",
            help="Focuser instrument to be used",
        )
        self.addParameters(
            dict(
                name="axis",
                long="axis",
                helpGroup="FOCUS",
                help="In case of multi-dimensional focuser, choose axis: X, Y, Z, U, V or W.",
                type=ParameterType.CHOICE,
                choices=["X", "Y", "Z", "U", "V", "W"],
                metavar="AXIS",
                default="Z",
            )
        )

        self.addController(
            name="autofocus",
            cls="Autofocus",
            required=False,
            helpGroup="FOCUS",
            help="Autofocus controller to be used",
        )

        self.addHelpGroup("AUTOFOCUS", "Autofocus")
        self.addParameters(
            dict(
                name="autofocus_step",
                long="step",
                type="int",
                helpGroup="AUTOFOCUS",
                help="Defines autofocus step.",
                metavar="STEP",
                default=500,
            ),
            dict(
                name="autofocus_exptime",
                short="-t",
                long="exptime",
                type="float",
                helpGroup="AUTOFOCUS",
                help="Defines autofocus frame exposure time.",
                metavar="EXPTIME",
                default=10.0,
            ),
            dict(
                name="autofocus_debug",
                long="debug",
                helpGroup="AUTOFOCUS",
                help="Run an autofocus debug session using data from PREVIOUS_RUN_DIR.",
                metavar="PREVIOUS_RUN_DIR",
                default="",
            ),
            dict(
                name="autofocus_nodisplay",
                long="disable-display",
                type=ParameterType.BOOLEAN,
                helpGroup="AUTOFOCUS",
                help="Disable interactive display during autofocus",
                default=False,
            ),
            dict(
                name="autofocus_filter",
                long="filter",
                helpGroup="AUTOFOCUS",
                help="Which filter to use in the autofocus run.",
                default="use-current-filter",
            ),
        )

        self.addHelpGroup("COMMANDS", "Commands")

    @parameter(
        long="range",
        helpGroup="AUTOFOCUS",
        default="1000-6000",
        help="Defines autofocus focuser range to be covered."
        "Use start-end, as in 1000-6000 to run from 1000 to 6000.",
        metavar="START-END",
    )
    def autofocus_range(self, value):
        r = re.compile(r"(?P<start>\d+)-(?P<end>\d+)")
        m = r.match(value)
        if not m:
            raise ValueError("Invalid start-end range")

        start, end = m.groups()
        start = int(start)
        end = int(end)
        return (start, end)

    @action(
        long="in", type="int", help="Move N steps IN", metavar="N", helpGroup="COMMANDS"
    )
    def move_in(self, options):
        self.out("Moving %s %d steps IN ... " % (options.axis, options.move_in), end="")

        try:
            self.focuser.moveIn(options.move_in, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position. Current position %d,"
                " target position %d, valid range %d-%d."
                % (
                    self.focuser.getPosition(),
                    self.focuser.getPosition() - int(options.move_in),
                    self.focuser.getRange()[0],
                    self.focuser.getRange()[1],
                )
            )

        self.out("OK")

        self._currentPosition(options)

    @action(
        long="out",
        type="int",
        help="Move N steps OUT",
        metavar="N",
        helpGroup="COMMANDS",
    )
    def move_out(self, options):
        self.out(
            "Moving %s %d steps OUT ... " % (options.axis, options.move_out), end=""
        )

        try:
            self.focuser.moveOut(options.move_out, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position. Current position %d,"
                " target position %d, valid range %d-%d."
                % (
                    self.focuser.getPosition(),
                    self.focuser.getPosition() + int(options.move_out),
                    self.focuser.getRange()[0],
                    self.focuser.getRange()[1],
                )
            )

        self.out("OK")

        self._currentPosition(options)

    @action(
        long="to",
        type="int",
        help="Move to POSITION",
        metavar="POSITION",
        helpGroup="COMMANDS",
    )
    def move_to(self, options):
        self.out("Moving %s to %d ... " % (options.axis, options.move_to), end="")

        try:
            self.focuser.moveTo(options.move_to, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position, must be between %d and %d," % self.focuser.getRange()
            )

        self.out("OK")

    @action(short="i", help="Print focuser current information", helpGroup="COMMANDS")
    def info(self, options):
        self.out("=" * 40)
        self.out(
            "Focuser: %s (%s)" % (self.focuser.getLocation(), self.focuser["device"])
        )
        self._currentPosition(options)
        self._validRange(options)

        if self.focuser.supports(FocuserFeature.TEMPERATURE_COMPENSATION):
            self.out("Temperature: %.2f oC" % self.focuser.getTemperature())

        if self.options.verbose:
            self.out("=" * 40)
            self.out("Supports:")
            for feature in FocuserFeature:
                self.out(
                    "\t%-25s" % str(feature), str(bool(self.focuser.supports(feature)))
                )
        self.out("=" * 40)

    @action(
        helpGroup="AUTOFOCUS",
        help="Start an autofocus session using the selected parameters."
        " You can select a focuser range and the size of the step for the sequence."
        " This option is exclusive, you cannot move manually at the same time.",
    )
    def auto(self, options):
        try:
            if not self.autofocus:
                self.exit(
                    "No Autofocus controller available. Try --autofocus=..., or --help."
                )
        except AttributeError:
            self.exit(
                "No Autofocus controller available. Try --autofocus=..., or --help."
            )

        ds9 = None

        if not options.autofocus_nodisplay:
            try:
                ds9 = DS9(open=True)
            except IOError:
                pass

        def stepComplete(position, star, filename):
            self.out(
                "#%04d (%4d, %4d) FWHM: %8.3f FLUX: %-9.3f (%s)"
                % (
                    position,
                    star["XWIN_IMAGE"],
                    star["YWIN_IMAGE"],
                    star["FWHM_IMAGE"],
                    star["FLUX_BEST"],
                    star["CHIMERA_FLAGS"],
                )
            )
            if ds9:
                ds9.displayFile(filename)
                ds9.set(
                    "regions command { circle %d %d %d}"
                    % (
                        int(star["XWIN_IMAGE"]),
                        int(star["YWIN_IMAGE"]),
                        int(star["FWHM_IMAGE"]),
                    )
                )
                ds9.set("zoom to fit")
                ds9.set("scale mode zscale")

        self.autofocus.stepComplete += stepComplete

        start, end = options.autofocus_range

        if options.autofocus_debug == "":
            debug = False
        else:
            debug = os.path.realpath(options.autofocus_debug)

        if options.autofocus_filter == "use-current-filter":
            filter = False
        else:
            filter = options.autofocus_filter

        try:
            if not debug:
                self.out(
                    "Looking for a star to focus on... (will try up to %d times) ..."
                    % self.autofocus["max_tries"]
                )

            result = self.autofocus.focus(
                exptime=options.autofocus_exptime,
                start=start,
                end=end,
                step=options.autofocus_step,
                minmax=(0, 30),
                debug=debug,
                filter=filter,
            )

            self.out("Best focus position found at %d." % result["best"])
            self.out("Moving focuser to %d .. OK" % result["best"])

        except IOError as e:
            self.exit(str(e))
        except FocusNotFoundException as e:
            self.exit(str(e))
        except StarNotFoundException as e:
            self.exit(str(e))
        except SExtractorException:
            self.exit(
                "Couldn't find SExtractor. If you have it installed, please add it to yout PATH variable."
            )
        except InvalidFilterPositionException as e:
            self.exit(str(e))

        time.sleep(1)

    def _currentPosition(self, options):
        self.out("Current focuser position: %s" % self.focuser.getPosition())

        for ax in ControllableAxis:
            if self.focuser.supports(ax) and ax != FocuserFeature.CONTROLLABLE_Z:
                self.out(
                    "\tAxis %s: %s"
                    % (
                        ControllableAxis[ax],
                        self.focuser.getPosition(ControllableAxis[ax]),
                    )
                )

        return

    def _validRange(self, options):
        self.out("Valid range: %s-%s" % self.focuser.getRange())

        for ax in ControllableAxis:
            if self.focuser.supports(ax) and ax != FocuserFeature.CONTROLLABLE_Z:
                self.out(
                    "\tRange %s: %s"
                    % (
                        ControllableAxis[ax],
                        self.focuser.getRange(ControllableAxis[ax]),
                    )
                )

        return


def main():
    cli = ChimeraFocus()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
