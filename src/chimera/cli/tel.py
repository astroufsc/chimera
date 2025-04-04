#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import copy
import sys

from chimera.core.exceptions import (
    ObjectNotFoundException,
    ObjectTooLowException,
    printException,
)
from chimera.core.version import _chimera_version_
from chimera.interfaces.fan import (
    FanControllabeDirection,
    FanControllabeSpeed,
    FanState,
    FanStatus,
)
from chimera.interfaces.telescope import (
    SlewRate,
    TelescopeCover,
    TelescopePier,
    TelescopePierSide,
    TelescopeStatus,
)
from chimera.util.coord import Coord
from chimera.util.output import green, red, yellow
from chimera.util.position import Position
from chimera.util.simbad import Simbad

from .cli import ChimeraCLI, ParameterType, action

# TODO: Abort, skip_init/init


class ChimeraTel(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-tel", "Telescope controller", _chimera_version_
        )

        self.localSlew = False

        self.addHelpGroup("TELESCOPE", "Telescope")
        self.addInstrument(
            name="telescope",
            cls="Telescope",
            required=True,
            help="Telescope instrument to be used. If blank, try to guess from chimera.config",
            helpGroup="TELESCOPE",
        )

        self.addHelpGroup("COORDS", "Coordinates")
        self.addParameters(
            dict(name="ra", type="string", helpGroup="COORDS", help="Right Ascension."),
            dict(name="dec", type="string", helpGroup="COORDS", help="Declination."),
            dict(
                name="epoch",
                type="string",
                default="J2000",
                helpGroup="COORDS",
                help="Epoch",
            ),
            dict(name="az", type="string", helpGroup="COORDS", help="Local Azimuth."),
            dict(name="alt", type="string", helpGroup="COORDS", help="Local Altitude."),
            dict(
                name="objectName",
                long="object",
                type="string",
                helpGroup="COORDS",
                help="Object name",
            ),
        )

        self.addHelpGroup("RATE", "Slew rate")
        self.addParameters(
            dict(
                name="rate",
                type=ParameterType.CHOICE,
                choices=[
                    "max",
                    "MAX",
                    "guide",
                    "GUIDE",
                    "center",
                    "CENTER",
                    "find",
                    "FIND",
                ],
                default="CENTER",
                helpGroup="RATE",
                help="Slew rate to be used for --move-* commands. GUIDE, CENTER, FIND or MAX",
            )
        )

        self.addHelpGroup("INIT", "Initialization")
        self.addHelpGroup("SLEW", "Slew")
        self.addHelpGroup("PARK", "Park")
        self.addHelpGroup("COVER", "Cover")
        self.addHelpGroup("PIERSIDE", "Side of Pier")
        self.addHelpGroup("TRACKING", "Tracking")
        self.addHelpGroup(
            "HANDLE",
            "Virtual Handle",
            "You can pass a int/float with number of arcseconds or use d:m:s notation. "
            "Remember that this is an offset relative to the current position.",
        )

        self.addHelpGroup("FANS", "Telescope fan control")
        self.addParameters(
            dict(
                name="fan",
                default="/Fan/0",
                helpGroup="FANS",
                help="Fan instrument to be used.",
            )
        )

    @action(help="Initialize the telescope (Lat/long/Date/Time)", helpGroup="INIT")
    def init(self, options):
        pass

    @action(help="Slew to given --ra --dec or --az --alt or --object", helpGroup="SLEW")
    def slew(self, options):
        telescope = self.telescope

        if options.objectName is not None:
            target = options.objectName
        else:
            target = self._validateCoords(options)

        def slewBegin(target):
            self.out(40 * "=")
            if options.objectName:
                coords = tuple(target)
                self.out(
                    "slewing to %s (%s %s %s)... "
                    % (options.objectName, coords[0], coords[1], target.epochString()),
                    end="",
                )
            else:
                self.out(
                    "slewing to %s (%s)... " % (target, target.epochString()), end=""
                )

        def slewComplete(position, status):
            if status == TelescopeStatus.OK:
                self.out("OK.")
                self.out(40 * "=")
            else:
                self.out("")

        telescope.slewBegin += slewBegin
        telescope.slewComplete += slewComplete

        if options.objectName:
            try:
                Simbad.lookup(target)
            except ObjectNotFoundException:
                self.err("Object '%s' not found on Simbad database." % target)
                self.exit()

        self.out(40 * "=")
        self.out("current position ra/dec: %s" % telescope.getPositionRaDec())
        self.out("current position alt/az: %s" % telescope.getPositionAltAz())

        try:
            if options.objectName:
                telescope.slewToObject(target)
            else:
                if self.localSlew:
                    telescope.slewToAltAz(target)
                else:
                    telescope.slewToRaDec(target)
        except ObjectTooLowException as e:
            self.err("ERROR: %s" % str(e))
            self.exit()

        self.out("new position ra/dec: %s" % telescope.getPositionRaDec())
        self.out("new position alt/az: %s" % telescope.getPositionAltAz())

        telescope.slewBegin -= slewBegin
        telescope.slewComplete -= slewComplete

    @action(help="Sync on the given --ra --dec or --object", helpGroup="SYNC")
    def sync(self, options):
        telescope = self.telescope

        if options.objectName is not None:
            target = options.objectName
        else:
            target = self._validateCoords(options)

        self.out(40 * "=")
        self.out("current position ra/dec: %s" % telescope.getPositionRaDec())
        self.out("current position:alt/az: %s" % telescope.getPositionAltAz())
        self.out(40 * "=")

        self.out("syncing on %s ... " % target, end="")

        if options.objectName:
            telescope.syncObject(options.objectName)
        else:
            telescope.syncRaDec(target)

        self.out("OK")

        self.out(40 * "=")
        self.out("new position ra/dec: %s" % telescope.getPositionRaDec())
        self.out("new position alt/az: %s" % telescope.getPositionAltAz())
        self.out(40 * "=")

    @action(help="Park the telescope", helpGroup="PARK", actionGroup="PARK")
    def park(self, options):
        self.out(40 * "=")
        self.out("parking ... ", end="")
        self.telescope.park()
        self.out("OK")
        self.out(40 * "=")

    @action(help="Unpark the telescope", helpGroup="PARK", actionGroup="PARK")
    def unpark(self, options):
        self.out(40 * "=")
        self.out("unparking ... ", end="")
        self.telescope.unpark()
        self.out("OK")
        self.out(40 * "=")

    @action(
        name="open_cover",
        help="Open telescope cover",
        long="open-cover",
        helpGroup="COVER",
        actionGroup="COVER",
    )
    def open(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopeCover):
            self.out("Telescope does not supports this action")
        else:
            self.out("Opening telescope cover ... ", end="")
            self.telescope.openCover()
            self.out("OK")

        self.out(40 * "=")

    @action(
        name="close_cover",
        help="Close telescope cover",
        long="close-cover",
        helpGroup="COVER",
        actionGroup="COVER",
    )
    def close(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopeCover):
            self.out("Telescope does not supports this action")
        else:
            self.out("Closing telescope cover ... ", end="")
            self.telescope.closeCover()
            self.out("OK")

        self.out(40 * "=")

    @action(
        name="stop_tracking",
        long="stop-tracking",
        help="Stop telescope tracking",
        helpGroup="TRACKING",
        actionGroup="TRACKING",
    )
    def stopTracking(self, options):
        self.out(40 * "=")
        self.out("stopping telescope tracking... ", end="")
        self.telescope.stopTracking()
        self.out("OK")
        self.out(40 * "=")

    @action(
        name="start_tracking",
        long="start-tracking",
        help="Start telescope tracking",
        helpGroup="TRACKING",
        actionGroup="TRACKING",
    )
    def startTracking(self, options):
        self.out(40 * "=")
        self.out("starting telescope tracking... ", end="")
        self.telescope.startTracking()
        self.out("OK")
        self.out(40 * "=")

    @action(
        long="fan-speed",
        type="float",
        help="Set fan speed.",
        metavar="speed",
        helpGroup="FANS",
        actionGroup="FANS",
    )
    def setFanSpeed(self, options):
        try:
            fan = self.telescope.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        self.out("=" * 40)
        self.out("Changing fan speed to %.2f " % (options.setFanSpeed), end=" ")
        try:
            fan.setRotation(options.setFanSpeed)
        except Exception as e:
            self.exit("%s. \n%s" % (red("FAILED"), printException(e)))

        self.out("%s" % (green("OK")))
        self.out("=" * 40)

    @action(
        long="fan-on", help="Start telescope fan", helpGroup="FANS", actionGroup="FANS"
    )
    def startFan(self, options):
        try:
            fan = self.telescope.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if fan.isSwitchedOn():
            self.exit("Fan is already running... ")

        self.out("=" * 40)

        self.out("Starting %s" % self.options.fan, end="")
        try:
            if fan.switchOn():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), printException(e)))

    @action(
        long="fan-off", help="Stop telescope fan", helpGroup="FANS", actionGroup="FANS"
    )
    def stopFan(self, options):
        try:
            fan = self.telescope.getManager().getProxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if not fan.isSwitchedOn():
            self.exit("Fan is not running... ")

        self.out("=" * 40)

        self.out("Stopping %s" % self.options.fan, end="")
        try:
            if fan.switchOff():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), printException(e)))

    @action(help="Print telescope information and exit")
    def info(self, options):
        telescope = self.telescope

        self.out(40 * "=")
        self.out("telescope: %s (%s)." % (telescope.getLocation(), telescope["device"]))

        position = telescope.getPositionRaDec()
        self.out("current position ra/dec (%s): %s" % (position.epoch, position))
        self.out("current position alt/az: %s" % telescope.getPositionAltAz())
        self.out("tracking: %s" % ("enabled" if telescope.isTracking() else "disabled"))
        if self.telescope.features(TelescopeCover):
            self.out(
                "telescope cover: %s "
                % ("open" if telescope.isCoverOpen() else "closed")
            )
        if self.telescope.features(TelescopePier):
            self.out(
                "current side of pier: %s " % telescope.getPierSide().__str__().lower()
            )

        if self.telescope["fans"] is not None:
            for fan in self.telescope["fans"]:
                fan = self.telescope.getManager().getProxy(fan)
                if fan.features(FanState):
                    st = fan.status()
                    if st == FanStatus.ON:
                        stats = green("ON")
                    elif st == FanStatus.OFF:
                        stats = red("OFF")
                    else:
                        stats = yellow(st.__str__())
                else:
                    stats = green("ON") if fan.isSwitchedOn() else red("OFF")
                rotation = (
                    " speed %.2f" % fan.getRotation()
                    if fan.features(FanControllabeSpeed)
                    else ""
                )
                direction = (
                    " direction %s" % fan.getDirection()
                    if fan.features(FanControllabeDirection)
                    else ""
                )
                self.out(
                    "Fan %s: %s%s%s" % (fan.getLocation(), stats, rotation, direction)
                )

        self.out(40 * "=")

    def _move(self, direction, cmd, offset):
        offset = self._validateOffset(offset)

        telescope = self.telescope

        self.out(40 * "=")
        self.out("current position ra/dec: %s" % telescope.getPositionRaDec())
        self.out("current position:alt/az: %s" % telescope.getPositionAltAz())

        self.out(40 * "=")
        self.out(
            "moving %s arcseconds (%s) %s at %s rate... "
            % (offset.AS, offset.strfcoord(), direction, self.options.rate),
            end="",
        )
        try:
            cmd(offset.AS, SlewRate(self.options.rate))
            self.out("OK")
            self.out(40 * "=")
            self.out("new position ra/dec: %s" % telescope.getPositionRaDec())
            self.out("new position:alt/az: %s" % telescope.getPositionAltAz())

        except Exception as e:
            self.err("ERROR. (%s)" % e)

        self.out(40 * "=")

    @action(
        name="move_east",
        short="E",
        long="move-east",
        type="string",
        help="Move telescope ARCSEC arcseconds to East.",
        metavar="ARCSEC",
        helpGroup="HANDLE",
    )
    def moveEast(self, options):
        self._move("East", self.telescope.moveEast, options.move_east)

    @action(
        name="move_west",
        short="W",
        long="move-west",
        type="string",
        help="Move telescope ARCSEC arcseconds to West.",
        metavar="ARCSEC",
        helpGroup="HANDLE",
    )
    def moveWest(self, options):
        self._move("West", self.telescope.moveWest, options.move_west)

    @action(
        name="move_north",
        short="N",
        long="move-north",
        type="string",
        help="Move telescope ARCSEC arcseconds to North.",
        metavar="ARCSEC",
        helpGroup="HANDLE",
    )
    def moveNorth(self, options):
        self._move("North", self.telescope.moveNorth, options.move_north)

    @action(
        name="move_south",
        short="S",
        long="move-south",
        type="string",
        help="Move telescope ARCSEC arcseconds to South.",
        metavar="ARCSEC",
        helpGroup="HANDLE",
    )
    def moveSouth(self, options):
        self._move("South", self.telescope.moveSouth, options.move_south)

    @action(
        help="Move telescope to EAST pierside",
        long="side-east",
        helpGroup="PIERSIDE",
        actionGroup="PIERSIDE",
    )
    def setPierSideEast(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopePier):
            self.out("Telescope does not supports this action")
        else:
            self.out("moving telescope to EAST pier side ... ", end="")
            self.telescope.setPierSide(TelescopePierSide.EAST)
            self.out("OK")

        self.out(40 * "=")

    @action(
        help="Move telescope to WEST pierside",
        long="side-west",
        helpGroup="PIERSIDE",
        actionGroup="PIERSIDE",
    )
    def setPierSideWest(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopePier):
            self.out("Telescope does not supports this action")
        else:
            self.out("moving telescope to WEST pier side ... ", end="")
            self.telescope.setPierSide(TelescopePierSide.WEST)
            self.out("OK")

        self.out(40 * "=")

    def _validateCoords(self, options):
        target = None

        if (options.ra is not None or options.dec is not None) and (
            options.az is not None or options.alt is not None
        ):
            self.exit(
                "RA/DEC and AZ/ALT given at the same time, I don't know what to do."
            )

        if (options.ra is not None) and (options.dec is not None):
            try:
                target = Position.fromRaDec(
                    options.ra, options.dec, epoch=options.epoch
                )
            except Exception as e:
                self.exit(str(e))

        elif (options.az is not None) and (options.alt is not None):
            try:
                target = Position.fromAltAz(options.alt, options.az)
                self.localSlew = True
            except Exception as e:
                self.exit(str(e))

        else:
            self.exit("Invalid coordinates, try --ra --dec or --alt --az or --object.")

        return target

    def __abort__(self):
        self.out("\naborting... ", end="")

        # create a copy of telescope proxy
        if hasattr(self, "telescope"):
            tel = copy.copy(self.telescope)
            tel.abortSlew()

    def _validateOffset(self, value):
        try:
            offset = Coord.fromAS(int(value))
        except ValueError:
            offset = Coord.fromDMS(value)

        return offset


def main():
    cli = ChimeraTel()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
