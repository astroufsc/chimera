#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import os
import re
import shutil
import string
import sys
import time
from textwrap import indent

import yaml
from astropy.time import Time

from chimera.controllers.scheduler.model import (
    Action,
    AutoFlat,
    AutoFocus,
    Expose,
    Point,
    PointVerify,
    Program,
    Session,
)
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.constants import DEFAULT_PROGRAM_DATABASE
from chimera.core.version import chimera_version
from chimera.util.coord import Coord
from chimera.util.output import blue, green, red
from chimera.util.position import Position

from .cli import ChimeraCLI, action

action_dict = {
    "autofocus": AutoFocus,
    "autoflat": AutoFlat,
    "pointverify": PointVerify,
    "point": Point,
    "expose": Expose,
}


class ChimeraSched(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-sched", "Scheduler controller", chimera_version
        )

        self.add_help_group("SCHEDULER", "Scheduler")
        self.add_controller(
            name="scheduler",
            cls="Scheduler",
            required=True,
            help="Scheduler controller to be used",
            help_group="SCHEDULER",
        )
        with open(
            os.path.dirname(__file__) + "/../controllers/scheduler/sample-sched.yaml"
        ) as f:
            example_yaml = f.read()
        with open(
            os.path.dirname(__file__) + "/../controllers/scheduler/sample-sched.txt"
        ) as f:
            example_txt = f.read()

        database_help = f"""Database options.

        The quickest and less configurable way to configure the scheduler database is to use
        a file with the following format:

{indent(example_txt, "        ")}
        
        It is also possible to use a ".yaml" file with the database configuration for each program. The file
        must have a .yaml extension so the script knows how to parse it.

{indent(example_yaml, "        ")}

        """

        self.add_help_group("DB", database_help)
        self.add_help_group("RUN", "Start/Stop/Info")

        self.add_parameters(
            dict(
                name="filename",
                long="file",
                short="f",
                help_group="DB",
                default="",
                help="Filename of the input database.",
                metavar="FILENAME",
            ),
            dict(
                name="output",
                short="o",
                type="string",
                help_group="DB",
                help="Images base filename including full path if needed.",
                default="$NAME-$DATE-$TIME",
            ),
        )

    @action(
        long="new",
        help="Generate a new database from a text file (excluding all programs already in database)",
        help_group="DB",
        action_group="DB",
    )
    def new_database(self, options):
        # save a copy
        if os.path.exists(DEFAULT_PROGRAM_DATABASE):
            shutil.copy(
                DEFAULT_PROGRAM_DATABASE,
                "%s.%s.bak" % (DEFAULT_PROGRAM_DATABASE, time.strftime("%Y%m%d%H%M%S")),
            )

        # delete all programs
        session = Session()
        programs = session.query(Program).all()
        for program in programs:
            session.delete(program)
        session.commit()

        self.generate_database(options)

    @action(
        long="append",
        help="Append programs to database from a text file",
        help_group="DB",
        action_group="DB",
    )
    def append_database(self, options):
        self.generate_database(options)

    def generate_database(self, options):
        if os.path.splitext(options.filename)[-1] == ".yaml":
            self._generate_database_yaml(options)
        else:
            self._generate_database_basic(options)

    def _generate_database_yaml(self, options):
        with open(options.filename) as stream:
            try:
                print("Loading %s" % options.filename, stream)
                prgconfig = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                self.exit(exc)

        session = Session()

        programs = []

        def _validate_offset(value):
            try:
                offset = Coord.from_as(int(value))
            except ValueError:
                offset = Coord.from_dms(value)

            return offset

        for prg in prgconfig["programs"]:
            # process program

            program = Program()
            for key in list(prg.keys()):
                if hasattr(program, key) and key != "actions":
                    if key == "start_at" and "T" in str(prg[key]):
                        prg[key] = Time(prg[key], format="isot").mjd
                    try:
                        setattr(program, key, prg[key])
                    # FIXME: remove noqa
                    except:  # noqa
                        self.err(
                            "Could not set attribute %s = %s on Program"
                            % (key, prg[key])
                        )

            self.out("# program: %s" % program.name)

            # process actions
            for actconfig in prg["actions"]:
                act = action_dict[actconfig["action"]]()
                self.out("Action: %s" % actconfig["action"])

                if actconfig["action"] == "point":
                    if "ra" in list(actconfig.keys()) and "dec" in list(
                        actconfig.keys()
                    ):
                        epoch = actconfig.get("epoch", "J2000")
                        position = Position.from_ra_dec(
                            actconfig["ra"], actconfig["dec"], epoch
                        )
                        self.out("\tCoords: %s" % position)
                        act.target_ra_dec = position
                    elif "alt" in list(actconfig.keys()) and "az" in list(
                        actconfig.keys()
                    ):
                        position = Position.from_alt_az(
                            actconfig["alt"], actconfig["az"]
                        )
                        self.out("\tCoords: %s" % position)
                        act.target_alt_az = position
                    elif "name" in actconfig:
                        self.out("\tTarget name: %s" % actconfig["name"])
                        act.target_name = actconfig["name"]

                    if (
                        "offset" not in actconfig
                        and "dome_az" not in actconfig
                        and "dome_tracking" not in actconfig
                        and "name" not in actconfig
                    ):
                        self.exit(
                            "[%s] Nothing to point at! %s" % (red("ERROR"), actconfig)
                        )

                    if "offset" in actconfig:
                        if "north" in actconfig["offset"]:
                            offset = _validate_offset(actconfig["offset"]["north"])
                            self.out("\tOffset north: %s" % offset)
                            act.offset_ns = offset
                        elif "south" in actconfig["offset"]:
                            offset = _validate_offset(actconfig["offset"]["south"])
                            self.out("\tOffset south: %s" % offset)
                            act.offset_ns = Coord.from_as(-offset.arcsec)

                        if "west" in actconfig["offset"]:
                            offset = _validate_offset(actconfig["offset"]["west"])
                            self.out("\tOffset west: %s" % offset)
                            act.offset_ew = offset
                        elif "east" in actconfig["offset"]:
                            offset = _validate_offset(actconfig["offset"]["east"])
                            self.out("\tOffset east: %s" % offset)
                            act.offset_ew = Coord.from_as(-offset.arcsec)

                    # Rotator position angle
                    if "pa" in actconfig:
                        act.pa = actconfig["pa"]
                        self.out("\tPA: %s" % act.pa)

                    # Special dome requirements... Needed mainly when doing dome FLATS.
                    if "dome_az" in actconfig:
                        actconfig["dome_az"] = Coord.from_dms(actconfig["dome_az"])
                        self.out("\tdome_az: %s" % actconfig["dome_az"])
                        act.dome_az = actconfig["dome_az"]
                    if "dome_tracking" in actconfig:
                        if actconfig["dome_tracking"] == "None":
                            actconfig["dome_tracking"] = None
                            self.out("\tDome tracking left AS IS")
                        elif actconfig["dome_tracking"]:
                            self.out("\tDome tracking ENABLED")
                        else:
                            self.out("\tDome tracking DISABLED")
                        act.dome_tracking = actconfig["dome_tracking"]

                else:
                    for key in list(actconfig.keys()):
                        if hasattr(act, key) and key != "action":
                            self.out("\t%s: %s" % (key, actconfig[key]))
                            try:
                                setattr(act, key, actconfig[key])
                            # FIXME: remove noqa
                            except:  # noqa
                                self.err(
                                    "Could not set attribute %s = %s on action %s"
                                    % (key, actconfig[key], actconfig["action"])
                                )
                program.actions.append(act)

            self.out("")
            programs.append(program)

        self.out("List contain %i programs" % len(programs))
        session.add_all(programs)
        session.commit()

        self.out("Restart the scheduler to run it with the new database.")

    def _generate_database_basic(self, options):
        f = None
        try:
            f = open(options.filename)
        # FIXME: remove noqa
        except:  # noqa
            self.exit("Could not find '%s'." % options.filename)

        session = Session()

        line_regex = re.compile(
            r"(?P<coord>(?P<ra>[\d:-]+)\s+(?P<dec>\+?[\d:-]+)\s+(?P<epoch>[\dnowNOWJjBb\.]+)\s+)?(?P<imagetype>[\w]+)"
            r'\s+(?P<objname>\'([^\\n\'\\\\]|\\\\.)*\'|"([^\\n"\\\\]|\\\\.)*"|([^ \\n"\\\\]|\\\\.)*)\s+(?P<exposures>[\w\d\s:\*\(\),]*)'
        )
        programs = []

        for i, line in enumerate(f):
            if line.startswith("#"):
                continue
            if len(line) == 1:
                continue

            matchs = line_regex.search(line)

            if matchs is None:
                print("Couldn't process line #%d" % i)
                continue

            params = matchs.groupdict()

            position = None
            objname = None

            if params.get("coord", None):
                position = Position.from_ra_dec(
                    params["ra"], params["dec"], params["epoch"]
                )

            imagetype = params["imagetype"].upper()
            objname = params["objname"].replace('"', "")

            multiplier, exps = params["exposures"].split("*")
            try:
                multiplier = int(multiplier)
            except ValueError:
                multiplier = 1

            exps = exps.replace("(", "").replace(")", "").strip().split(",")

            for i in range(multiplier):
                program = Program(name="%s-%03d" % (objname.replace(" ", ""), i))

                self.out("# program: %s" % program.name)

                if imagetype == "OBJECT":
                    if position:
                        program.actions.append(Point(target_ra_dec=position))
                    else:
                        program.actions.append(Point(target_name=objname))

                        # if imagetype == "FLAT":
                        #     site = self._remote_manager.get_proxy("/Site/0")
                        #     flat_position = Position.from_alt_az(site['flat_alt'], site['flat_az'])
                        #     program.actions.append(Point(target_alt_az=flat_position))
                        # TODO: point dome to its flat position too.

                for exp in exps:
                    if exp.count(":") > 1:
                        filter, exptime, frames = exp.strip().split(":")
                    else:
                        filter, exptime = exp.strip().split(":")
                        frames = 1

                    if imagetype in ("OBJECT", "FLAT"):
                        shutter = "OPEN"
                    else:
                        shutter = "CLOSE"

                    if imagetype == "BIAS":
                        exptime = 0

                    if imagetype in ("BIAS", "DARK"):
                        filter = None

                    self.out(
                        "%s %s %s filter=%s exptime=%s frames=%s"
                        % (imagetype, objname, str(position), filter, exptime, frames)
                    )

                    program.actions.append(
                        Expose(
                            shutter=shutter,
                            filename=string.Template(options.output).safe_substitute(
                                {"NAME": objname.replace(" ", "")}
                            ),
                            filter=filter,
                            frames=frames,
                            exptime=exptime,
                            image_type=imagetype,
                            object_name=objname,
                        )
                    )
                self.out("")
                programs.append(program)

        session.add_all(programs)
        session.commit()

        self.out("Restart the scheduler to run it with the new database.")

    @action(help="Start the scheduler", help_group="RUN", action_group="RUN")
    def start(self, options):
        self.out("=" * 40)
        self.out("Starting ...", end="")
        self.scheduler.start()
        self.out("%s" % green("OK"))
        self.out("=" * 40)
        self.monitor(options)

    @action(help="Stop the scheduler", help_group="RUN", action_group="RUN")
    def stop(self, options):
        self.scheduler.stop()
        self.out("OK")

    @action(help="Restart the scheduler", help_group="RUN", action_group="RUN")
    def restart(self, options):
        self.out("=" * 40)
        self.out("Restarting ...", end="")
        self.scheduler.stop()
        self.scheduler.start()
        self.out("%s" % green("OK"))
        self.out("=" * 40)
        self.monitor(options)

    @action(help="Print scheduler information", help_group="RUN")
    def info(self, options):
        self.out("=" * 40)
        self.out("Scheduler: %s" % self.scheduler.get_location())
        self.out("State: %s" % self.scheduler.state())
        if self.scheduler.state() == State.BUSY and self.scheduler.current_action():
            session = Session()
            action = session.merge(self.scheduler.current_action())
            program = (
                session.query(Program).filter(Program.id == action.program_id).one()
            )
            self.out("Working on: %s (%s)" % (program.name, str(action)))

        self.out("=" * 40)

    @action(help="Monitor scheduler actions", help_group="RUN")
    def monitor(self, options):
        def program_begin_clbk(program_id):
            session = Session()
            program = session.query(Program).filter(Program.id == program_id).one()
            program = session.merge(program)
            self.out("=" * 40)
            self.out("%s %s" % (blue("[program]"), program.name))

        def program_complete_clbk(program_id, status, message=None):
            session = Session()
            program = session.query(Program).filter(Program.id == program_id).one()
            program = session.merge(program)
            if status == SchedulerStatus.OK:
                self.out(
                    "%s %s %s" % (blue("[program]"), program.name, green(str(status)))
                )
            else:
                self.out(
                    "%s %s %s (%s)"
                    % (
                        blue("[program]"),
                        program.name,
                        red(str(status)),
                        red(str(message)),
                    )
                )

        def action_begin_clbk(action_id, message):
            session = Session()
            action = session.query(Action).filter(Action.id == action_id).one()
            action = session.merge(action)
            self.out("%s %s ..." % (blue("[action] "), message), end="")

        def action_complete_clbk(action_id, status, message=None):
            session = Session()
            action = session.query(Action).filter(Action.id == action_id).one()

            if status == SchedulerStatus.OK:
                self.out("%s" % green(str(status)))
            else:
                self.out("%s (%s)" % (red(str(status)), red(str(message))))

        def state_changed_clbk(new_state, old_state):
            if new_state == State.OFF:
                self.out("=" * 40)
                self.out("%s finished all programs" % blue("[scheduler]"))
                self.out("=" * 40)

        self.scheduler.program_begin += program_begin_clbk
        self.scheduler.program_complete += program_complete_clbk
        self.scheduler.action_begin += action_begin_clbk
        self.scheduler.action_complete += action_complete_clbk
        self.scheduler.state_changed += state_changed_clbk

        if self.scheduler.state() == State.OFF:
            self.out("%s no programs to do" % blue("[scheduler]"))

        while True:
            if self.scheduler.state() == State.OFF:
                self.exit()
            time.sleep(0.1)


def main():
    cli = ChimeraSched()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
