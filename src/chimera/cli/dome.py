#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import copy
import functools
import sys
from typing import cast

from chimera.core.exceptions import print_exception
from chimera.core.proxy import Proxy
from chimera.core.url import resolve_url
from chimera.core.version import chimera_version
from chimera.interfaces.dome import Mode
from chimera.interfaces.fan import (
    Fan,
    FanControllableDirection,
    FanControllableSpeed,
    FanState,
    FanStatus,
)
from chimera.interfaces.lamp import IntensityOutOfRangeException, Lamp, LampDimmer
from chimera.util.output import green, red, yellow

from .cli import ChimeraCLI, action


class ChimeraDome(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(self, "chimera-dome", "Dome controller", chimera_version)

        self.add_help_group("DOME", "Dome")
        self.add_instrument(
            name="dome",
            cls="Dome",
            required=True,
            help="Dome instrument to be used",
            help_group="DOME",
        )

        self.add_help_group("DOMEFANS", "Dome fan control")
        self.add_parameters(
            dict(
                name="fan",
                default="/Fan/0",
                help_group="DOMEFANS",
                help="Fan instrument to be used.",
            )
        )

        self.add_help_group("TELESCOPE", "Telescope Tracking Configuration")
        self.add_parameters(
            dict(
                name="telescope",
                default="/Telescope/0",
                help_group="TELESCOPE",
                help="Tell the dome to follow TELESCOPE when tracking"
                "(only utilized when using --track",
            )
        )

        self.add_help_group("LIGHT", "Dome lights control")
        self.add_parameters(
            dict(
                name="lamp",
                default="/Lamp/0",
                help_group="LIGHT",
                help="Calibration lamp to be used.",
            )
        )

        self.add_help_group("COMMANDS", "Commands")
        self.add_help_group("SHUTTER", "Shutter")
        self.add_help_group("DOMEFANS", "Dome Fans control")

    @action(
        long="open-slit",
        help="Open dome slit",
        help_group="SHUTTER",
        action_group="SLIT",
    )
    def open_slit(self, options):
        self.out("Opening dome slit ... ", end="")
        self.dome.open_slit()
        self.out("OK")

    @action(
        long="close-slit",
        help="Close dome slit",
        help_group="SHUTTER",
        action_group="SLIT",
    )
    def close_slit(self, options):
        self.out("Closing dome slit ... ", end="")
        self.dome.close_slit()
        self.out("OK")

    @action(
        long="open-flap",
        help="Open dome flap",
        help_group="SHUTTER",
        action_group="FLAP",
    )
    def open_flap(self, options):
        self.out("Opening dome flap ... ", end="")
        self.dome.open_flap()
        self.out("OK")

    @action(
        long="close-flap",
        help="Close dome flap",
        help_group="SHUTTER",
        action_group="FLAP",
    )
    def close_flap(self, options):
        self.out("Closing dome flap ... ", end="")
        self.dome.close_flap()
        self.out("OK")

    @action(
        long="light-off",
        help="Turn light off",
        help_group="LIGHT",
        action_group="LIGHT",
    )
    def light_off(self, options):
        self.out("Turning light off ... ", end="")
        self.lamp().switch_off()
        self.out(green("OK"))

    @action(
        long="light-on", help="Turn light on", help_group="LIGHT", action_group="LIGHT"
    )
    def light_on(self, options):
        self.out("Turning light on ... ", end="")
        self.lamp().switch_on()
        self.out(green("OK"))

    @action(
        long="light-intensity",
        type="float",
        metavar="intensity",
        help="Set light intensity to specified value.",
        help_group="LIGHT",
        action_group="LIGHT",
    )
    def intensity(self, options):
        self.out("Setting light intensity to %.2f ... " % options.intensity, end="")
        try:
            if not self.lamp().is_switched_on():
                self.exit("%s: Cannot set intensity with lamp OFF." % red("ERROR"))
            if self.lamp().features("LampDimmer"):
                self.lamp().set_intensity(options.intensity)
            else:
                self.exit("Lamp does not support light intensity setting.")
        except IntensityOutOfRangeException:
            self.exit(
                "\n%s: Intensity out of range: %s" % (red("ERROR"), lamp.get_range())
            )

        self.out(green("OK"))

    @action(help="Track the telescope", help_group="TELESCOPE", action_group="TRACKING")
    def track(self, options):
        if options.telescope:
            self.dome["telescope"] = options.telescope

        self.out("Activating tracking ... ", end="")
        self.dome.track()
        self.out("OK")

    @action(
        help="Stop tracking the telescope (stand)",
        help_group="TELESCOPE",
        action_group="TRACKING",
    )
    def stand(self, options):
        self.out("Deactivating tracking ... ", end="")
        self.dome.stand()
        self.out("OK")

    @action(
        long="to",
        type="string",
        help="Move dome to AZ azimuth",
        metavar="AZ",
        help_group="COMMANDS",
    )
    def move_to(self, options):
        try:
            target = float(options.move_to)
        except ValueError as e:
            self.exit(f"Invalid azimuth: '{options.move_to}' [{e}]")

        self.out(f"Moving dome to {target} ... ", end="")
        self.dome.slew_to_az(target)
        self.out("OK")

    @action(
        long="fan-speed",
        type="float",
        help="Set fan speed.",
        metavar="speed",
        help_group="DOMEFANS",
        action_group="DOMEFANS",
    )
    def set_fan_speed(self, options):
        self.out("=" * 40)
        self.out("Changing fan speed to %.2f " % (options.set_fan_speed), end=" ")
        try:
            self.fan().set_rotation(options.set_fan_speed)
        except Exception as e:
            self.exit("%s. \n%s" % (red("FAILED"), print_exception(e)))

        self.out("%s" % (green("OK")))
        self.out("=" * 40)

    # @functools.cached_property
    def fan(self) -> Fan:
        fan_proxy = Proxy(
            resolve_url(self.options.fan, bus=self.dome.get_location()), bus=self.bus
        )
        if not fan_proxy.ping():
            self.exit(f"{red('ERROR')}: Could not find fan '{self.options.fan}.")
        return cast(Fan, fan_proxy)

    # @functools.cached_property
    def lamp(self) -> Fan:
        lamp_proxy = Proxy(
            resolve_url(self.options.lamp, bus=self.dome.get_location()), bus=self.bus
        )
        if not lamp_proxy.ping():
            self.exit(f"{red('ERROR')}: Could not find lamp '{self.options.lamp}.")
        return cast(Lamp, lamp_proxy)

    @action(
        long="fan-on",
        help="Start dome fan",
        help_group="DOMEFANS",
        action_group="DOMEFANS",
    )
    def start_fan(self, options):
        if self.fan().is_switched_on():
            self.exit("Fan is already running... ")

        self.out("=" * 40)

        self.out("Starting %s" % self.options.fan, end="")
        try:
            if self.fan().switch_on():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), print_exception(e)))

    @action(
        long="fan-off",
        help="Stop dome fan",
        help_group="DOMEFANS",
        action_group="DOMEFANS",
    )
    def stop_fan(self, options):
        if not self.fan().is_switched_on():
            self.exit("Fan is not running... ")

        self.out("=" * 40)

        self.out("Stopping %s" % self.options.fan, end="")
        try:
            if self.fan().switch_off():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), print_exception(e)))

    @action(help="Print dome information", help_group="COMMANDS")
    def info(self, options):
        self.out("=" * 40)
        self.out("Dome: %s (%s)." % (self.dome.get_location(), self.dome["device"]))

        self.out("Current dome azimuth: %s." % self.dome.get_az())
        self.out("Current dome mode: %s." % self.dome.get_mode())

        if self.dome.get_mode() == Mode.Track:
            self.out("Tracking: %s." % self.dome["telescope"])

        if self.dome.is_slit_open():
            self.out("Dome slit is open.")
        else:
            self.out("Dome slit is closed.")

        if self.dome["lamps"] is not None:
            for lamp in self.dome["lamps"]:
                onoff = green("ON") if self.lamp().is_switched_on() else red("OFF")
                dimming = (
                    " intensity: %3.2f" % self.lamp().get_intensity()
                    if self.lamp().features("LampDimmer")
                    else ""
                )
                self.out(
                    "Lamp %s: %s %s" % (self.lamp().get_location(), onoff, dimming)
                )

        if self.dome["fans"] is not None:
            for fan in self.dome["fans"]:
                if self.fan().features("FanState"):
                    st = self.fan().status()
                    if st == FanStatus.ON:
                        stats = green("ON")
                    elif st == FanStatus.OFF:
                        stats = red("OFF")
                    else:
                        stats = yellow(st.__str__())
                else:
                    stats = green("ON") if self.fan().is_switched_on() else red("OFF")
                rotation = (
                    " speed %.2f" % self.fan().get_rotation()
                    if self.fan().features("FanControllableSpeed")
                    else ""
                )
                direction = (
                    " direction %s" % self.fan().get_direction()
                    if self.fan().features("FanControllableDirection")
                    else ""
                )
                self.out(
                    "Fan %s: %s%s%s"
                    % (self.fan().get_location(), stats, rotation, direction)
                )

        self.out("=" * 40)

    def __abort__(self):
        self.out("\naborting... ", endl="")

        # copy self.dome Proxy because we are running from a different thread
        if hasattr(self, "dome"):
            dome = copy.copy(self.dome)
            dome.abort_slew()


def main():
    cli = ChimeraDome()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
