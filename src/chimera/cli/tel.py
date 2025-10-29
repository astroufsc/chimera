#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import sys

from chimera.core.exceptions import (
    ObjectNotFoundException,
    ObjectTooLowException,
    print_exception,
)
from chimera.core.version import chimera_version
from chimera.interfaces.fan import (
    FanControllableDirection,
    FanControllableSpeed,
    FanState,
    FanStatus,
)
from chimera.interfaces.telescope import (
    Telescope,
    TelescopeCover,
    TelescopePier,
    TelescopePierSide,
    TelescopeStatus,
)
from chimera.util.coord import Coord
from chimera.util.output import green, red, yellow
from chimera.util.position import Position

from .cli import ChimeraCLI, action


class ChimeraTel(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-tel", "Telescope controller", chimera_version
        )

        self.local_slew = False

        self.add_help_group("TELESCOPE", "Telescope")
        self.add_instrument(
            name="telescope",
            cls="Telescope",
            required=True,
            help="Telescope instrument to be used. If blank, try to guess from chimera.config",
            help_group="TELESCOPE",
        )

        self.add_help_group("COORDS", "Coordinates")
        self.add_parameters(
            dict(
                name="ra", type="string", help_group="COORDS", help="Right Ascension."
            ),
            dict(name="dec", type="string", help_group="COORDS", help="Declination."),
            dict(
                name="epoch",
                type=float,
                default=2000,
                help_group="COORDS",
                help="Epoch",
            ),
            dict(name="az", type="string", help_group="COORDS", help="Local Azimuth."),
            dict(
                name="alt", type="string", help_group="COORDS", help="Local Altitude."
            ),
            dict(
                name="object_name",
                long="object",
                type="string",
                help_group="COORDS",
                help="Object name",
            ),
        )

        self.add_help_group("RATE", "Slew rate")
        self.add_parameters(
            dict(
                name="rate",
                type="float",
                default=None,
                help_group="RATE",
                help="Slew rate to be used for --move-* commands in Arcseconds per second. If None, use the default rate.",
            )
        )

        self.add_help_group("INIT", "Initialization")
        self.add_help_group("SLEW", "Slew")
        self.add_help_group("PARK", "Park")
        self.add_help_group("COVER", "Cover")
        self.add_help_group("PIERSIDE", "Side of Pier")
        self.add_help_group("TRACKING", "Tracking")
        self.add_help_group(
            "HANDLE",
            "Virtual Handle",
            "You can pass a int/float with number of arcseconds or use d:m:s notation. "
            "Remember that this is an offset relative to the current position.",
        )

        self.add_help_group("FANS", "Telescope fan control")
        self.add_parameters(
            dict(
                name="fan",
                default="/Fan/0",
                help_group="FANS",
                help="Fan instrument to be used.",
            )
        )

    def _print_current_position(self, tag="current"):
        ra, dec = self.telescope.get_position_ra_dec()
        alt, az = self.telescope.get_position_alt_az()
        self.out(
            f"{tag} position ra/dec: {Coord.from_h(ra).to_hms()}/{Coord.from_d(dec).to_dms()}"
        )
        self.out(
            f"{tag} position alt/az: {Coord.from_d(alt).to_dms()}/{Coord.from_h(az).to_hms()}"
        )

    @action(
        help="Slew to given --ra --dec or --az --alt or --object", help_group="SLEW"
    )
    def slew(self, options):
        telescope: Telescope = self.telescope

        if options.object_name is not None:
            target = options.object_name
        else:
            target = self._validate_coords(options)

        def slew_begin(ra, dec):
            self.out(40 * "=")
            if options.object_name:
                self.out(
                    f"slewing to {options.object_name} ({Coord.from_h(ra).to_hms()} {Coord.from_d(dec).to_dms()})... ",
                    end="",
                )
            else:
                self.out(f"slewing to {target} ({target.epoch_string()})... ", end="")

        def slew_complete(ra, dec, status):
            if status == TelescopeStatus.OK:
                self.out("OK.")
                self.out(40 * "=")
            else:
                self.out("")

        # FIXME: this won't work as we cannot resolve these methods!
        telescope.slew_begin += slew_begin
        telescope.slew_complete += slew_complete

        self.out(40 * "=")
        self._print_current_position()

        try:
            if options.object_name:
                try:
                    telescope.slew_to_object(target)
                except ObjectNotFoundException:
                    self.err(f"Object '{target}' not found on Simbad database.")
                    self.exit()
            else:
                if self.local_slew:
                    telescope.slew_to_alt_az(target.alt, target.az)
                else:
                    ra, dec = target
                    telescope.slew_to_ra_dec(ra, dec, epoch=2000.0)
        except ObjectTooLowException as e:
            self.err("ERROR: %s" % str(e))
            self.exit()

        self._print_current_position("new")

        telescope.slew_begin -= slew_begin
        telescope.slew_complete -= slew_complete

    @action(help="Sync on the given --ra --dec or --object", help_group="SYNC")
    def sync(self, options):
        telescope = self.telescope

        if options.object_name is not None:
            target = options.object_name
        else:
            target = self._validate_coords(options)

        self.out(40 * "=")
        self._print_current_position()
        self.out(40 * "=")

        self.out("syncing on %s ... " % target, end="")

        if options.object_name:
            telescope.sync_object(options.object_name)
        else:
            telescope.sync_ra_dec(target)

        self.out("OK")

        self.out(40 * "=")
        self._print_current_position("new")
        self.out(40 * "=")

    @action(help="Park the telescope", help_group="PARK", action_group="PARK")
    def park(self, options):
        self.out(40 * "=")
        self.out("parking ... ", end="")
        self.telescope.park()
        self.out("OK")
        self.out(40 * "=")

    @action(help="Unpark the telescope", help_group="PARK", action_group="PARK")
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
        help_group="COVER",
        action_group="COVER",
    )
    def open(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopeCover):
            self.out("Telescope does not supports this action")
        else:
            self.out("Opening telescope cover ... ", end="")
            self.telescope.open_cover()
            self.out("OK")

        self.out(40 * "=")

    @action(
        name="close_cover",
        help="Close telescope cover",
        long="close-cover",
        help_group="COVER",
        action_group="COVER",
    )
    def close(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopeCover):
            self.out("Telescope does not supports this action")
        else:
            self.out("Closing telescope cover ... ", end="")
            self.telescope.close_cover()
            self.out("OK")

        self.out(40 * "=")

    @action(
        name="stop_tracking",
        long="stop-tracking",
        help="Stop telescope tracking",
        help_group="TRACKING",
        action_group="TRACKING",
    )
    def stop_tracking(self, options):
        self.out(40 * "=")
        self.out("stopping telescope tracking... ", end="")
        self.telescope.stop_tracking()
        self.out("OK")
        self.out(40 * "=")

    @action(
        name="start_tracking",
        long="start-tracking",
        help="Start telescope tracking",
        help_group="TRACKING",
        action_group="TRACKING",
    )
    def start_tracking(self, options):
        self.out(40 * "=")
        self.out("starting telescope tracking... ", end="")
        self.telescope.start_tracking()
        self.out("OK")
        self.out(40 * "=")

    @action(
        long="fan-speed",
        type="float",
        help="Set fan speed.",
        metavar="speed",
        help_group="FANS",
        action_group="FANS",
    )
    def set_fan_speed(self, options):
        try:
            fan = self.telescope.get_proxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        self.out("=" * 40)
        self.out("Changing fan speed to %.2f " % (options.set_fan_speed), end=" ")
        try:
            fan.set_rotation(options.set_fan_speed)
        except Exception as e:
            self.exit("%s. \n%s" % (red("FAILED"), print_exception(e)))

        self.out("%s" % (green("OK")))
        self.out("=" * 40)

    @action(
        long="fan-on",
        help="Start telescope fan",
        help_group="FANS",
        action_group="FANS",
    )
    def start_fan(self, options):
        try:
            fan = self.telescope.get_proxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if fan.is_switched_on():
            self.exit("Fan is already running... ")

        self.out("=" * 40)

        self.out("Starting %s" % self.options.fan, end="")
        try:
            if fan.switch_on():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), print_exception(e)))

    @action(
        long="fan-off",
        help="Stop telescope fan",
        help_group="FANS",
        action_group="FANS",
    )
    def stop_fan(self, options):
        try:
            fan = self.telescope.get_proxy(options.fan)
        except ObjectNotFoundException:
            self.exit("%s: Could not find requested fan." % red("ERROR"))

        if not fan.is_switched_on():
            self.exit("Fan is not running... ")

        self.out("=" * 40)

        self.out(f"Stopping {self.options.fan}", end="")
        try:
            if fan.switch_off():
                self.out(green("OK"))
            else:
                self.out(red("FAILED"))
            self.out("=" * 40)
        except Exception as e:
            self.exit("%s\n %s" % (red("FAILED"), print_exception(e)))

    @action(help="Print telescope information and exit")
    def info(self, options):
        telescope = self.telescope

        self.out(40 * "=")
        self.out(f"telescope: {telescope.get_location()}, device={telescope['device']}")

        ra, dec = telescope.get_position_ra_dec()
        self._print_current_position()
        self.out(
            "tracking: %s" % ("enabled" if telescope.is_tracking() else "disabled")
        )
        if self.telescope.features("TelescopeCover"):
            self.out(
                "telescope cover: %s "
                % ("open" if telescope.is_cover_open() else "closed")
            )
        if self.telescope.features("TelescopePier"):
            self.out(
                "current side of pier: %s "
                % telescope.get_pier_side().__str__().lower()
            )

        if self.telescope["fans"] is not None:
            for fan in self.telescope["fans"]:
                fan = self.telescope.get_proxy(fan)
                if fan.features(FanState):
                    st = fan.status()
                    if st == FanStatus.ON:
                        stats = green("ON")
                    elif st == FanStatus.OFF:
                        stats = red("OFF")
                    else:
                        stats = yellow(st.__str__())
                else:
                    stats = green("ON") if fan.is_switched_on() else red("OFF")
                rotation = (
                    " speed %.2f" % fan.get_rotation()
                    if fan.features(FanControllableSpeed)
                    else ""
                )
                direction = (
                    " direction %s" % fan.get_direction()
                    if fan.features(FanControllableDirection)
                    else ""
                )
                self.out(
                    "Fan %s: %s%s%s" % (fan.get_location(), stats, rotation, direction)
                )

        self.out(40 * "=")

    def _move(self, direction, cmd, offset):
        offset = self._validate_offset(offset)

        self.out(40 * "=")
        self._print_current_position()
        self.out(40 * "=")
        self.out(
            "moving %s arcseconds (%s) %s at %s arcsec/sec rate... "
            % (offset.arcsec, offset.strfcoord(), direction, self.options.rate),
            end="",
        )
        try:
            cmd(offset.arcsec, self.options.rate)
            self.out("OK")
            self.out(40 * "=")
            self._print_current_position("new")

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
        help_group="HANDLE",
    )
    def move_east(self, options):
        self._move("East", self.telescope.move_east, options.move_east)

    @action(
        name="move_west",
        short="W",
        long="move-west",
        type="string",
        help="Move telescope ARCSEC arcseconds to West.",
        metavar="ARCSEC",
        help_group="HANDLE",
    )
    def move_west(self, options):
        self._move("West", self.telescope.move_west, options.move_west)

    @action(
        name="move_north",
        short="N",
        long="move-north",
        type="string",
        help="Move telescope ARCSEC arcseconds to North.",
        metavar="ARCSEC",
        help_group="HANDLE",
    )
    def move_north(self, options):
        self._move("North", self.telescope.move_north, options.move_north)

    @action(
        name="move_south",
        short="S",
        long="move-south",
        type="string",
        help="Move telescope ARCSEC arcseconds to South.",
        metavar="ARCSEC",
        help_group="HANDLE",
    )
    def move_south(self, options):
        self._move("South", self.telescope.move_south, options.move_south)

    @action(
        help="Move telescope to EAST pierside",
        long="side-east",
        help_group="PIERSIDE",
        action_group="PIERSIDE",
    )
    def set_pier_side_east(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopePier):
            self.out("Telescope does not supports this action")
        else:
            self.out("moving telescope to EAST pier side ... ", end="")
            self.telescope.set_pier_side(TelescopePierSide.EAST)
            self.out("OK")

        self.out(40 * "=")

    @action(
        help="Move telescope to WEST pierside",
        long="side-west",
        help_group="PIERSIDE",
        action_group="PIERSIDE",
    )
    def set_pier_side_west(self, options):
        self.out(40 * "=")

        if not self.telescope.features(TelescopePier):
            self.out("Telescope does not supports this action")
        else:
            self.out("moving telescope to WEST pier side ... ", end="")
            self.telescope.set_pier_side(TelescopePierSide.WEST)
            self.out("OK")

        self.out(40 * "=")

    def _validate_coords(self, options):
        target = None

        if (options.ra is not None or options.dec is not None) and (
            options.az is not None or options.alt is not None
        ):
            self.exit(
                "RA/DEC and AZ/ALT given at the same time, I don't know what to do."
            )

        if (options.ra is not None) and (options.dec is not None):
            try:
                if options.epoch != 2000:
                    self.out("ERROR: epoch %s is not supported." % options.epoch)
                    self.exit()
                # target = Position.from_ra_dec(options.ra, options.dec)  # todo: epoch
                target = (options.ra, options.dec)
            except Exception as e:
                self.exit(str(e))

        elif (options.az is not None) and (options.alt is not None):
            try:
                target = Position.from_alt_az(options.alt, options.az)
                self.local_slew = True
            except Exception as e:
                self.exit(str(e))

        else:
            self.exit("Invalid coordinates, try --ra --dec or --alt --az or --object.")

        return target

    def __abort__(self):
        self.out("\naborting... ", end="")

        if hasattr(self, "telescope"):
            self.telescope.abort_slew()

    def _validate_offset(self, value):
        try:
            offset = Coord.from_as(int(value))
        except ValueError:
            offset = Coord.from_dms(value)

        return offset


def main():
    cli = ChimeraTel()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
