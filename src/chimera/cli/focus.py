#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import os
import re
import sys
import time

from chimera.core.version import chimera_version
from chimera.interfaces.autofocus import FocusNotFoundException, StarNotFoundException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.interfaces.focuser import (
    ControllableAxis,
    FocuserAxis,
    FocuserFeature,
    InvalidFocusPositionException,
)
from chimera.util.ds9 import DS9
from chimera.util.sextractor import SExtractorError

from .cli import ChimeraCLI, ParameterType, action, parameter


class ChimeraFocus(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-focus", "Focuser controller", chimera_version
        )

        self.add_help_group("FOCUS", "Focus")
        self.add_instrument(
            name="focuser",
            cls="Focuser",
            required=True,
            help_group="FOCUS",
            help="Focuser instrument to be used",
        )
        self.add_parameters(
            dict(
                name="axis",
                long="axis",
                help_group="FOCUS",
                help="In case of multi-dimensional focuser, choose axis: X, Y, Z, U, V or W.",
                type=ParameterType.CHOICE,
                choices=["X", "Y", "Z", "U", "V", "W"],
                metavar="AXIS",
                default="Z",
            )
        )

        self.add_controller(
            name="autofocus",
            cls="Autofocus",
            required=False,
            help_group="FOCUS",
            help="Autofocus controller to be used",
        )

        self.add_help_group("AUTOFOCUS", "Autofocus")
        self.add_parameters(
            dict(
                name="autofocus_step",
                long="step",
                type="int",
                help_group="AUTOFOCUS",
                help="Defines autofocus step.",
                metavar="STEP",
                default=500,
            ),
            dict(
                name="autofocus_exptime",
                short="-t",
                long="exptime",
                type="float",
                help_group="AUTOFOCUS",
                help="Defines autofocus frame exposure time.",
                metavar="EXPTIME",
                default=10.0,
            ),
            dict(
                name="autofocus_debug",
                long="debug",
                help_group="AUTOFOCUS",
                help="Run an autofocus debug session using data from PREVIOUS_RUN_DIR.",
                metavar="PREVIOUS_RUN_DIR",
                default="",
            ),
            dict(
                name="autofocus_nodisplay",
                long="disable-display",
                type=ParameterType.BOOLEAN,
                help_group="AUTOFOCUS",
                help="Disable interactive display during autofocus",
                default=False,
            ),
            dict(
                name="autofocus_filter",
                long="filter",
                help_group="AUTOFOCUS",
                help="Which filter to use in the autofocus run.",
                default="use-current-filter",
            ),
        )

        self.add_help_group("COMMANDS", "Commands")

    @parameter(
        long="range",
        help_group="AUTOFOCUS",
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
        long="in",
        type="int",
        help="Move N steps IN",
        metavar="N",
        help_group="COMMANDS",
    )
    def move_in(self, options):
        self.out("Moving %s %d steps IN ... " % (options.axis, options.move_in), end="")

        try:
            self.focuser.move_in(options.move_in, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position. Current position %d,"
                " target position %d, valid range %d-%d."
                % (
                    self.focuser.get_position(),
                    self.focuser.get_position() - int(options.move_in),
                    self.focuser.get_range()[0],
                    self.focuser.get_range()[1],
                )
            )

        self.out("OK")

        self._current_position(options)

    @action(
        long="out",
        type="int",
        help="Move N steps OUT",
        metavar="N",
        help_group="COMMANDS",
    )
    def move_out(self, options):
        self.out(
            "Moving %s %d steps OUT ... " % (options.axis, options.move_out), end=""
        )

        try:
            self.focuser.move_out(options.move_out, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position. Current position %d,"
                " target position %d, valid range %d-%d."
                % (
                    self.focuser.get_position(),
                    self.focuser.get_position() + int(options.move_out),
                    self.focuser.get_range()[0],
                    self.focuser.get_range()[1],
                )
            )

        self.out("OK")

        self._current_position(options)

    @action(
        long="to",
        type="int",
        help="Move to POSITION",
        metavar="POSITION",
        help_group="COMMANDS",
    )
    def move_to(self, options):
        self.out("Moving %s to %d ... " % (options.axis, options.move_to), end="")

        try:
            self.focuser.move_to(options.move_to, FocuserAxis(options.axis))
        except InvalidFocusPositionException:
            self.exit(
                "Invalid position, must be between %d and %d,"
                % self.focuser.get_range()
            )

        self.out("OK")

    @action(short="i", help="Print focuser current information", help_group="COMMANDS")
    def info(self, options):
        self.out("=" * 40)
        self.out(
            "Focuser: %s (%s)" % (self.focuser.get_location(), self.focuser["device"])
        )
        self._current_position(options)
        self._valid_range(options)

        if self.focuser.supports(FocuserFeature.TEMPERATURE_COMPENSATION):
            self.out("Temperature: %.2f oC" % self.focuser.get_temperature())

        if self.options.verbose:
            self.out("=" * 40)
            self.out("Supports:")
            for feature in FocuserFeature:
                self.out(
                    "\t%-25s" % str(feature), str(bool(self.focuser.supports(feature)))
                )
        self.out("=" * 40)

    @action(
        help_group="AUTOFOCUS",
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
            except OSError:
                pass

        def step_complete(position, star, filename):
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
                ds9.display_file(filename)
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

        self.autofocus.step_complete += step_complete

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

        except OSError as e:
            self.exit(str(e))
        except FocusNotFoundException as e:
            self.exit(str(e))
        except StarNotFoundException as e:
            self.exit(str(e))
        except SExtractorError:
            self.exit(
                "Couldn't find SExtractor. If you have it installed, please add it to yout PATH variable."
            )
        except InvalidFilterPositionException as e:
            self.exit(str(e))

        time.sleep(1)

    def _current_position(self, options):
        self.out("Current focuser position: %s" % self.focuser.get_position())

        for ax in ControllableAxis:
            if self.focuser.supports(ax) and ax != FocuserFeature.CONTROLLABLE_Z:
                self.out(
                    "\tAxis %s: %s"
                    % (
                        ControllableAxis[ax],
                        self.focuser.get_position(ControllableAxis[ax]),
                    )
                )

        return

    def _valid_range(self, options):
        min, max = self.focuser.get_range()
        self.out(f"Valid range: [{min}, {max}]")

        for ax in ControllableAxis:
            if self.focuser.supports(ax) and ax != FocuserFeature.CONTROLLABLE_Z:
                self.out(
                    "\tRange %s: %s"
                    % (
                        ControllableAxis[ax],
                        self.focuser.get_range(ControllableAxis[ax]),
                    )
                )

        return


def main():
    cli = ChimeraFocus()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
