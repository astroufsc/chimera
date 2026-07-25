#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import sys

from chimera.core.version import chimera_version
from chimera.interfaces.focuser import (
    ControllableAxis,
    FocuserAxis,
    FocuserFeature,
    InvalidFocusPositionException,
)

from .cli import ChimeraCLI, ParameterType, action


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

        self.add_help_group("COMMANDS", "Commands")

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
