#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.cli import ChimeraCLI, action
from chimera.core.exceptions import ObjectNotFoundException
from chimera.interfaces.fan import (
    FanControllabeSpeed,
    FanControllabeDirection,
    FanStatus,
    FanState,
)
from chimera.util.coord import Coord
from chimera.core.exceptions import printException
from chimera.util.output import green, red, yellow
from chimera.interfaces.dome import Mode
from chimera.interfaces.lamp import IntensityOutOfRangeException, LampDimmer
import sys
import copy


class ChimeraDome(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(self, "chimera-dome", "Dome controller", 0.1)

        self.addHelpGroup("DOME", "Dome")
        self.addInstrument(
            name="dome",
            cls="Dome",
            required=True,
            help="Dome instrument to be used",
            helpGroup="DOME",
        )

        self.addHelpGroup("DOMEFANS", "Dome fan control")
        self.addParameters(
            dict(
                name="fan",
                default="/Fan/0",
                helpGroup="DOMEFANS",
                help="Fan instrument to be used.",
            )
        )

        self.addHelpGroup("TELESCOPE", "Telescope Tracking Configuration")
        self.addParameters(
            dict(
                name="telescope",
                default="/Telescope/0",
                helpGroup="TELESCOPE",
                help="Tell the dome to follow TELESCOPE when tracking"
                "(only utilized when using --track",
            )
        )

        self.addHelpGroup("LIGHT", "Dome lights control")
        self.addParameters(
            dict(
                name="lamp",
                default="/Lamp/0",
                helpGroup="LIGHT",
                help="Calibration lamp to be used.",
            )
        )

        self.addHelpGroup("COMMANDS", "Commands")
        self.addHelpGroup("SHUTTER", "Shutter")
        self.addHelpGroup("DOMEFANS", "Dome Fans control")

    @action(
        long="open-slit", help="Open dome slit", helpGroup="SHUTTER", actionGroup="SLIT"
    )
    def openSlit(self, options):
        self.out("Opening dome slit ... ", end="")
        self.dome.openSlit()
        self.out("OK")

    @action(
        long="close-slit",
        help="Close dome slit",
        helpGroup="SHUTTER",
        actionGroup="SLIT",
    )
    def closeSlit(self, options):
        self.out("Closing dome slit ... ", end="")
        self.dome.closeSlit()
        self.out("OK")

    @action(
        long="open-flap", help="Open dome flap", helpGroup="SHUTTER", actionGroup="FLAP"
    )
    def openFlap(self, options):
        self.out("Opening dome flap ... ", end="")
        self.dome.openFlap()
        self.out("OK")

    @action(
        long="close-flap",
        help="Close dome flap",
        helpGroup="SHUTTER",
        actionGroup="FLAP",
    )
    def closeFlap(self, options):
        self.out("Closing dome flap ... ", end="")
        self.dome.closeFlap()
        self.out("OK")

    @action(
        long="light-off", help="Turn light off", helpGroup="LIGHT", actionGroup="LIGHT"
    )
    def lightOff(self, options):
        self.out("Turning light off ... ", end="")

        try:
            lamp = self.dome.getManager().getProxy(options.lamp)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested calibration lamp." % red("ERROR"))
        lamp.switchOff()
        self.out(green("OK"))

    @action(
        long="light-on", help="Turn light on", helpGroup="LIGHT", actionGroup="LIGHT"
    )
    def lightOn(self, options):
        self.out("Turning light on ... ", end="")
        try:
            lamp = self.dome.getManager().getProxy(options.lamp)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested calibration lamp." % red("ERROR"))

        lamp.switchOn()
        self.out(green("OK"))

    @action(
        long="light-intensity",
        type="float",
        metavar="intensity",
        help="Set light intensity to specified value.",
        helpGroup="LIGHT",
        actionGroup="LIGHT",
    )
    def intensity(self, options):
        self.out("Setting light intensity to %.2f ... " % options.intensity, end="")

        # lamp = None
        # try:
        try:
            lamp = self.dome.getManager().getProxy(options.lamp)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested calibration lamp." % red("ERROR"))
        try:
            if not lamp.isSwitchedOn():
                self.exit("%s: Cannot set intensity with lamp OFF." % red("ERROR"))
            if lamp.features(LampDimmer):
                lamp.setIntensity(options.intensity)
            else:
                self.exit("Lamp does not support light intensity setting.")
        # except ObjectNotFoundException, e:
        #     self.exit('%s: Could not find requested calibration lamp.' % red('ERROR'))
        except IntensityOutOfRangeException:
            self.exit(
                "\n%s: Intensity out of range: %s" % (red("ERROR"), lamp.getRange())
            )
        # except Exception, e:
        #     self.exit('%s: (%s).' % (red('ERROR'), printException(e)))

        self.out(green("OK"))

    @action(help="Track the telescope", helpGroup="TELESCOPE", actionGroup="TRACKING")
    def track(self, options):

        if options.telescope:
            self.dome["telescope"] = options.telescope

        self.out("Activating tracking ... ", end="")
        self.dome.track()
        self.out("OK")

    @action(
        help="Stop tracking the telescope (stand)",
        helpGroup="TELESCOPE",
        actionGroup="TRACKING",
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
        helpGroup="COMMANDS",
    )
    def moveTo(self, options):

        try:
            target = Coord.fromDMS(options.moveTo)
        except ValueError as e:
            self.exit("Invalid azimuth (%s)" % e)

        self.out("Moving dome to %s ... " % target, end="")
        self.dome.slewToAz(target)
        self.out("OK")

    @action(
        long="fan-speed",
        type="float",
        help="Set fan speed.",
        metavar="speed",
        helpGroup="DOMEFANS",
        actionGroup="DOMEFANS",
    )
    def setFanSpeed(self, options):
        try:
            domefan = self.dome.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        self.out("=" * 40)
        self.out("Changing fan speed to %.2f " % (options.setFanSpeed), end=" ")
        try:
            domefan.setRotation(options.setFanSpeed)
        except Exception as e:
            self.exit("%s. \n%s" % (red("FAILED"), printException(e)))

        self.out("%s" % (green("OK")))
        self.out("=" * 40)

    @action(
        long="fan-on",
        help="Start dome fan",
        helpGroup="DOMEFANS",
        actionGroup="DOMEFANS",
    )
    def startFan(self, options):

        try:
            domefan = self.dome.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if domefan.isSwitchedOn():
            self.exit("Fan is already running... ")

        self.out("=" * 40)

        self.out("Starting %s" % self.options.fan, end="")
        try:
            if domefan.switchOn():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), printException(e)))

    @action(
        long="fan-off",
        help="Stop dome fan",
        helpGroup="DOMEFANS",
        actionGroup="DOMEFANS",
    )
    def stopFan(self, options):

        try:
            domefan = self.dome.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if not domefan.isSwitchedOn():
            self.exit("Fan is not running... ")

        self.out("=" * 40)

        self.out("Stopping %s" % self.options.fan, end="")
        try:
            if domefan.switchOff():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), printException(e)))

    @action(help="Print dome information", helpGroup="COMMANDS")
    def info(self, options):

        self.out("=" * 40)
        self.out("Dome: %s (%s)." % (self.dome.getLocation(), self.dome["device"]))

        self.out("Current dome azimuth: %s." % self.dome.getAz())
        self.out("Current dome mode: %s." % self.dome.getMode())

        if self.dome.getMode() == Mode.Track:
            self.out("Tracking: %s." % self.dome["telescope"])

        if self.dome.isSlitOpen():
            self.out("Dome slit is open.")
        else:
            self.out("Dome slit is closed.")

        if self.dome["lamps"] is not None:
            for lamp in self.dome["lamps"]:
                lamp = self.dome.getManager().getProxy(lamp)
                onoff = green("ON") if lamp.isSwitchedOn() else red("OFF")
                dimming = (
                    " intensity: %3.2f" % lamp.getIntensity()
                    if lamp.features(LampDimmer)
                    else ""
                )
                self.out("Lamp %s: %s %s" % (lamp.getLocation(), onoff, dimming))

        if self.dome["fans"] is not None:
            for fan in self.dome["fans"]:
                domefan = self.dome.getManager().getProxy(fan)
                if domefan.features(FanState):
                    st = domefan.status()
                    if st == FanStatus.ON:
                        stats = green("ON")
                    elif st == FanStatus.OFF:
                        stats = red("OFF")
                    else:
                        stats = yellow(st.__str__())
                else:
                    stats = green("ON") if domefan.isSwitchedOn() else red("OFF")
                rotation = (
                    " speed %.2f" % domefan.getRotation()
                    if domefan.features(FanControllabeSpeed)
                    else ""
                )
                direction = (
                    " direction %s" % domefan.getDirection()
                    if domefan.features(FanControllabeDirection)
                    else ""
                )
                self.out(
                    "Fan %s: %s%s%s"
                    % (domefan.getLocation(), stats, rotation, direction)
                )

        self.out("=" * 40)

    def __abort__(self):
        self.out("\naborting... ", endl="")

        # copy self.dome Proxy because we are running from a different thread
        if hasattr(self, "dome"):
            dome = copy.copy(self.dome)
            dome.abortSlew()


def main():
    cli = ChimeraDome()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
