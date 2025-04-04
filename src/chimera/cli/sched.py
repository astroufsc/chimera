#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import os
import re
import shutil
import string
import sys
import time

import yaml
from astropy.time import Time

from chimera.controllers.scheduler.model import (
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
from chimera.core.version import _chimera_version_
from chimera.util.coord import Coord
from chimera.util.output import blue, green, red
from chimera.util.position import Position

from .cli import ChimeraCLI, action

actionDict = {
    "autofocus": AutoFocus,
    "autoflat": AutoFlat,
    "pointverify": PointVerify,
    "point": Point,
    "expose": Expose,
}


class ChimeraSched(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-sched", "Scheduler controller", _chimera_version_
        )

        self.addHelpGroup("SCHEDULER", "Scheduler")
        self.addController(
            name="scheduler",
            cls="Scheduler",
            required=True,
            help="Scheduler controller to be used",
            helpGroup="SCHEDULER",
        )

        databaseHelp = """Database options.

        The quickest and less configurable way to configure the scheduler database is to use
        a file with the following format:

        # RA      dec       epoch  type    name  N*(f1:t1:n1, f2:t2:n2, ......)
        14:00:00 -30:00:00  J2000  OBJECT  obj1  2*(V:7, R:6:2, B:5:2)
        15:00:00 -30:00:00  NOW    OBJECT  obj2  2*(V:7, R:6:2, B:5:2)

        # special targets follow different format
        # for bias and dark, filter is ignored, we use same format just to keep it simple

        # type name       N[*(f1:t1:n1, ...)]
        FLAT   flat       3*(V:10:1, R:8:2, B:9:3)
        BIAS   bias       1*(V:0)
        DARK   dark       1*(V:1:4)
        OBJECT \"NGC 5272\" 1*(B:10:10)

        It is also possible to use a ".yaml" file with the database configuration for each program. The file
        must have a .yaml extension so the script knows how to parse it.

        programs:
            # You can configure each database to its fullest.

            -   program:
                name: PRG01           # (optional)
                pi: Tiago Ribeiro     # (optional)
                priority: 1           # (optional)
                startAt: 57500.030    # Program start time in MJD or in ISO 8601 (yyyy-MM-ddTHH:mm:ss) (optional)
                validFor: 50 #s       # Program only valid for N seconds after startAt (optional)

                # Add actions in the order they are intended to be performed.
                actions:
                    -   action: point
                        ra: "14:00:00"
                        dec: "-30:00:00"
                        epoch: J2000
                        offset:
                            south: 600 # arcsec
                            east: 300 # arcsec

                    -   action: autofocus
                        start: 100
                        end: 200
                        step: 10
                        filter: R
                        exptime: 10
                        compress_format: fits_rice   # Enable output file compression

                    -   action: pointverify
                        here: True

                    -   action: expose
                        filter: V
                        frames: 1
                        exptime: 7
                        imageType: OBJECT
                        objectName: obj1 acq
                        wait_dome: False        # Do not wait to dome sync to take the exposure

                    -   action: expose
                        filter: R
                        frames: 2
                        exptime: 6
                        imageType: OBJECT
                        objectName: obj1 acq

                    -   action: expose
                        filter: B
                        frames: 2
                        exptime: 5
                        imageType: OBJECT
                        objectName: obj1 acq

            # new target with no autofocus or pointverify
            -   program:
                name: PRG02
                pi: William Schoenell
                priority: 2
                actions:
                    -   action: point
                        ra: "15:00:00"
                        dec: "-30:00:00"
                        epoch: NOW

                    -   action: expose
                        filter: V
                        frames: 1
                        exptime: 7
                        imageType: OBJECT
                        objectName: obj1 acq

                    -   action: expose
                        filter: R
                        frames: 2
                        exptime: 6
                        imageType: OBJECT
                        objectName: obj1 acq

                    -   action: expose
                        filter: B
                        frames: 2
                        exptime: 5
                        imageType: OBJECT
                        objectName: obj1 acq

            # Point to a target name
            -   program:
                name: PROG03
                pi: Antonio Kanaan
                priority: 3
                actions:
                    -   action: point
                        name: "NGC 5272"

                    -   action: expose
                        filter: B
                        frames: 10
                        exptime: 10
                        imageType: OBJECT
                        objectName: "NGC 5272"

        # calibrations

            -   program:
                name: DAYLIGHT CALIBRATIONS
                pi: Tiago Ribeiro
                actions:
                    # BIAS
                    -   action: expose
                        frames: 10
                        imageType: BIAS  # This will set shutter to close

                    # DARK
                    -   action: expose
                        frames: 10
                        exptime: 100
                        imageType: DARK  # This will set shutter to close already

                    # LIGHT DARK
                    -   action: expose
                        frames: 10
                        exptime: 100
                        shutter: OPEN    # In case you want to take light dark, you can specify shutter to be open
                        imageType: DARK

                    # FLAT FIELD
                    -   action: point
                        alt: "80:00:00"
                        az: "10:00:00"
                        domeAz: "112:00:00"
                        domeTracking: False

                    -   action: expose
                        frames: 10
                        filter: V
                        exptime: 10
                        imageType: FLAT

                    -   action: expose
                        frames: 10
                        filter: R
                        exptime: 8
                        imageType: FLAT

                    -   action: expose
                        frames: 9
                        filter: B
                        exptime: 20
                        imageType: FLAT

                    -   action: point
                        domeTracking: True   # Restart dome tracking

        """

        self.addHelpGroup("DB", databaseHelp)
        self.addHelpGroup("RUN", "Start/Stop/Info")

        self.addParameters(
            dict(
                name="filename",
                long="file",
                short="f",
                helpGroup="DB",
                default="",
                help="Filename of the input database.",
                metavar="FILENAME",
            ),
            dict(
                name="output",
                short="o",
                type="string",
                helpGroup="DB",
                help="Images base filename including full path if needed.",
                default="$NAME-$DATE-$TIME",
            ),
        )

    @action(
        long="new",
        help="Generate a new database from a text file (excluding all programs already in database)",
        helpGroup="DB",
        actionGroup="DB",
    )
    def newDatabase(self, options):
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

        self.generateDatabase(options)

    @action(
        long="append",
        help="Append programs to database from a text file",
        helpGroup="DB",
        actionGroup="DB",
    )
    def appendDatabase(self, options):
        self.generateDatabase(options)

    def generateDatabase(self, options):
        if os.path.splitext(options.filename)[-1] == ".yaml":
            self._generateDatabase_yaml(options)
        else:
            self._generateDatabase_basic(options)

    def _generateDatabase_yaml(self, options):
        with open(options.filename, "r") as stream:
            try:
                prgconfig = yaml.load(stream)
            except yaml.YAMLError as exc:
                self.exit(exc)

        session = Session()

        programs = []

        def _validateOffset(value):
            try:
                offset = Coord.fromAS(int(value))
            except ValueError:
                offset = Coord.fromDMS(value)

            return offset

        for prg in prgconfig["programs"]:
            # process program

            program = Program()
            for key in list(prg.keys()):
                if hasattr(program, key) and key != "actions":
                    if key == "startAt" and "T" in prg[key]:
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
                act = actionDict[actconfig["action"]]()
                self.out("Action: %s" % actconfig["action"])

                if actconfig["action"] == "point":
                    if "ra" in list(actconfig.keys()) and "dec" in list(
                        actconfig.keys()
                    ):
                        epoch = (
                            "J2000"
                            if "epoch" not in list(actconfig.keys())
                            else actconfig["epoch"]
                        )
                        position = Position.fromRaDec(
                            actconfig["ra"], actconfig["dec"], epoch
                        )
                        self.out("\tCoords: %s" % position)
                        act.targetRaDec = position
                        # act = Point(targetRaDec=position)
                    elif "alt" in list(actconfig.keys()) and "az" in list(
                        actconfig.keys()
                    ):
                        position = Position.fromAltAz(actconfig["alt"], actconfig["az"])
                        self.out("\tCoords: %s" % position)
                        act.targetAltAz = position
                    elif "name" in actconfig:
                        self.out("\tTarget name: %s" % actconfig["name"])
                        act.targetName = actconfig["name"]

                    if (
                        "offset" not in actconfig
                        and "domeAz" not in actconfig
                        and "domeTracking" not in actconfig
                        and "name" not in actconfig
                    ):
                        self.exit("[%s] Nothing to point at!" % red("ERROR"))

                    if "offset" in actconfig:
                        if "north" in actconfig["offset"]:
                            offset = _validateOffset(actconfig["offset"]["north"])
                            self.out("\tOffset north: %s" % offset)
                            act.offsetNS = offset
                        elif "south" in actconfig["offset"]:
                            offset = _validateOffset(actconfig["offset"]["south"])
                            self.out("\tOffset south: %s" % offset)
                            act.offsetNS = Coord.fromAS(-offset.AS)

                        if "west" in actconfig["offset"]:
                            offset = _validateOffset(actconfig["offset"]["west"])
                            self.out("\tOffset west: %s" % offset)
                            act.offsetEW = offset
                        elif "east" in actconfig["offset"]:
                            offset = _validateOffset(actconfig["offset"]["east"])
                            self.out("\tOffset east: %s" % offset)
                            act.offsetEW = Coord.fromAS(-offset.AS)

                    # Special dome requirements... Needed mainly when doing dome FLATS.
                    if "domeAz" in actconfig:
                        actconfig["domeAz"] = Coord.fromDMS(actconfig["domeAz"])
                        self.out("\tdomeAz: %s" % actconfig["domeAz"])
                        act.domeAz = actconfig["domeAz"]
                    if "domeTracking" in actconfig:
                        if actconfig["domeTracking"] == "None":
                            actconfig["domeTracking"] = None
                            self.out("\tDome tracking left AS IS")
                        elif actconfig["domeTracking"]:
                            self.out("\tDome tracking ENABLED")
                        else:
                            self.out("\tDome tracking DISABLED")
                        act.domeTracking = actconfig["domeTracking"]

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

    def _generateDatabase_basic(self, options):
        f = None
        try:
            f = open(options.filename, "r")
        # FIXME: remove noqa
        except:  # noqa
            self.exit("Could not find '%s'." % options.filename)

        session = Session()

        lineRe = re.compile(
            r"(?P<coord>(?P<ra>[\d:-]+)\s+(?P<dec>\+?[\d:-]+)\s+(?P<epoch>[\dnowNOWJjBb\.]+)\s+)?(?P<imagetype>[\w]+)"
            r'\s+(?P<objname>\'([^\\n\'\\\\]|\\\\.)*\'|"([^\\n"\\\\]|\\\\.)*"|([^ \\n"\\\\]|\\\\.)*)\s+(?P<exposures>[\w\d\s:\*\(\),]*)'
        )
        programs = []

        for i, line in enumerate(f):
            if line.startswith("#"):
                continue
            if len(line) == 1:
                continue

            matchs = lineRe.search(line)

            if matchs is None:
                print("Couldn't process line #%d" % i)
                continue

            params = matchs.groupdict()

            position = None
            objname = None

            if params.get("coord", None):
                position = Position.fromRaDec(
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
                        program.actions.append(Point(targetRaDec=position))
                    else:
                        program.actions.append(Point(targetName=objname))

                        # if imagetype == "FLAT":
                        #     site = self._remoteManager.getProxy("/Site/0")
                        #     flatPosition = Position.fromAltAz(site['flat_alt'], site['flat_az'])
                        #     program.actions.append(Point(targetAltAz=flatPosition))
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
                            imageType=imagetype,
                            objectName=objname,
                        )
                    )
                self.out("")
                programs.append(program)

        session.add_all(programs)
        session.commit()

        self.out("Restart the scheduler to run it with the new database.")

    @action(help="Start the scheduler", helpGroup="RUN", actionGroup="RUN")
    def start(self, options):
        self.out("=" * 40)
        self.out("Starting ...", end="")
        self.scheduler.start()
        self.out("%s" % green("OK"))
        self.out("=" * 40)
        self.monitor(options)

    @action(help="Stop the scheduler", helpGroup="RUN", actionGroup="RUN")
    def stop(self, options):
        self.scheduler.stop()
        self.out("OK")

    @action(help="Restart the scheduler", helpGroup="RUN", actionGroup="RUN")
    def restart(self, options):
        self.out("=" * 40)
        self.out("Restarting ...", end="")
        self.scheduler.stop()
        self.scheduler.start()
        self.out("%s" % green("OK"))
        self.out("=" * 40)
        self.monitor(options)

    @action(help="Print scheduler information", helpGroup="RUN")
    def info(self, options):
        self.out("=" * 40)
        self.out("Scheduler: %s" % self.scheduler.getLocation())
        self.out("State: %s" % self.scheduler.state())
        if self.scheduler.state() == State.BUSY and self.scheduler.currentAction():
            session = Session()
            action = session.merge(self.scheduler.currentAction())
            program = (
                session.query(Program).filter(Program.id == action.program_id).one()
            )
            self.out("Working on: %s (%s)" % (program.name, str(action)))

        self.out("=" * 40)

    @action(help="Monitor scheduler actions", helpGroup="RUN")
    def monitor(self, options):
        def programBeginClbk(program):
            session = Session()
            program = session.merge(program)
            self.out("=" * 40)
            self.out("%s %s" % (blue("[program]"), program.name))

        def programCompleteClbk(program, status, message=None):
            session = Session()
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

        def actionBeginClbk(action, message):
            session = Session()
            action = session.merge(action)
            self.out("%s %s ..." % (blue("[action] "), message), end="")

        def actionCompleteClbk(action, status, message=None):
            session = Session()
            action = session.merge(action)

            if status == SchedulerStatus.OK:
                self.out("%s" % green(str(status)))
            else:
                self.out("%s (%s)" % (red(str(status)), red(str(message))))

        def stateChangedClbk(newState, oldState):
            if newState == State.OFF:
                self.out("=" * 40)
                self.out("%s finished all programs" % blue("[scheduler]"))
                self.out("=" * 40)
                self.exit()

        self.scheduler.programBegin += programBeginClbk
        self.scheduler.programComplete += programCompleteClbk
        self.scheduler.actionBegin += actionBeginClbk
        self.scheduler.actionComplete += actionCompleteClbk
        self.scheduler.stateChanged += stateChangedClbk

        if self.scheduler.state() == State.OFF:
            self.out("%s no programs to do" % blue("[scheduler]"))
        else:
            self.wait(abort=False)


def main():
    cli = ChimeraSched()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
