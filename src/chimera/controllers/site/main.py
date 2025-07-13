# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import os.path
import logging
import optparse
import sys
import platform

from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.systemconfig import SystemConfig
from chimera.core.version import _chimera_version_
from chimera.core.exceptions import (
    print_exception,
    InvalidLocationException,
    ChimeraException,
)
from chimera.core.constants import (
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
    SYSTEM_CONFIG_DEFAULT_FILENAME,
)

from chimera.core.site import Site
from chimera.core.path import ChimeraPath

import chimera.core.log


log = logging.getLogger(__name__)


class SiteController(object):

    def __init__(self, args=[], wait=True):

        self.wait = wait

        self.options, self.args = self.parse_args(args)

        if self.options.verbose == 1:
            chimera.core.log.set_console_level(logging.INFO)
            # log.set_console_level(logging.INFO)

        if self.options.verbose > 1:
            chimera.core.log.set_console_level(logging.DEBUG)
            # log.set_console_level(logging.DEBUG)

        self.paths = {"instruments": [], "controllers": []}

        # add system and plugins paths
        path = ChimeraPath()
        self.paths["instruments"].extend(path.instruments)
        self.paths["controllers"].extend(path.controllers)

    def parse_args(self, args):

        def check_location(option, opt_str, value, parser):
            try:
                Location(value)
            except InvalidLocationException:
                raise optparse.OptionValueError(f"{value} isnt't a valid location.")

            eval(f'parser.values.{option.dest}.append ("{value}")')

        def check_includepath(option, opt_str, value, parser):

            if not value or not os.path.isdir(os.path.abspath(value)):
                raise optparse.OptionValueError(f"Couldn't found {value} include path.")

            eval(f'parser.values.{option.dest}.append ("{value}")')

        parser = optparse.OptionParser(
            prog="chimera",
            version=_chimera_version_,
            usage="chimera --help for more information",
        )

        manag_group = optparse.OptionGroup(parser, "Basic options")
        manag_group.add_option(
            "-H",
            "--host",
            action="store",
            dest="host",
            type="string",
            help="Host name/IP address to run as; [default=%default]",
            metavar="HOST",
        )

        manag_group.add_option(
            "-P",
            "--port",
            action="store",
            dest="port",
            type="string",
            help="Port on which to listen for requests; [default=%default]",
            metavar="PORT",
        )

        config_group = optparse.OptionGroup(parser, "Configuration")

        config_group.add_option(
            "--config",
            dest="config_file",
            help="Start Chimera using configuration from FILE.",
            metavar="FILE",
        )

        config_group.add_option(
            "--daemon",
            action="store_true",
            dest="daemon",
            help="Run Chimera in Daemon mode (will detach from current terminal).",
        )

        misc_group = optparse.OptionGroup(parser, "General")

        misc_group.add_option(
            "--dry-run",
            action="store_true",
            dest="dry",
            help="Only list all configured objects (from command line and configuration files) without starting the system.",
        )

        misc_group.add_option(
            "-v",
            "--verbose",
            action="count",
            dest="verbose",
            help="Increase log level (multiple v's to increase even more).",
        )

        inst_group = optparse.OptionGroup(
            parser, "Instruments and Controllers Management"
        )

        inst_group.add_option(
            "-i",
            "--instrument",
            action="callback",
            callback=check_location,
            dest="instruments",
            type="string",
            help="Load the instrument defined by LOCATION."
            "This option could be set many times to load multiple instruments.",
            metavar="LOCATION",
        )

        inst_group.add_option(
            "-c",
            "--controller",
            action="callback",
            callback=check_location,
            dest="controllers",
            type="string",
            help="Load the controller defined by LOCATION."
            "This option could be set many times to load multiple controllers.",
            metavar="LOCATION",
        )

        inst_group.add_option(
            "-I",
            "--instruments-dir",
            action="callback",
            callback=check_includepath,
            dest="inst_dir",
            type="string",
            help="Append PATH to instruments load path.",
            metavar="PATH",
        )

        inst_group.add_option(
            "-C",
            "--controllers-dir",
            action="callback",
            callback=check_includepath,
            dest="ctrl_dir",
            type="string",
            help="Append PATH to controllers load path.",
            metavar="PATH",
        )

        parser.add_option_group(manag_group)
        parser.add_option_group(config_group)
        parser.add_option_group(misc_group)
        parser.add_option_group(inst_group)

        parser.set_defaults(
            instruments=[],
            controllers=[],
            config_file=SYSTEM_CONFIG_DEFAULT_FILENAME,
            inst_dir=[],
            ctrl_dir=[],
            drv_dir=[],
            dry=False,
            verbose=0,
            daemon=False,
            host=MANAGER_DEFAULT_HOST,
            port=MANAGER_DEFAULT_PORT,
        )

        return parser.parse_args(args)

    def startup(self):
        # system config
        try:
            self.config = SystemConfig.from_file(self.options.config_file)
        except (InvalidLocationException, IOError) as e:
            log.exception(e)
            log.error(f"There was a problem reading your configuration file. ({e})")
            sys.exit(1)

        # manager
        if not self.options.dry:
            log.info("Starting system.")
            log.info(f"Chimera: {_chimera_version_}")
            log.info(f"Chimera prefix: {ChimeraPath().root()}")
            log.info(f"Python: {platform.python_version()}")
            log.info("System: {}".format(" ".join(platform.uname())))

            try:
                self.manager = Manager(**self.config.chimera)
            except ChimeraException:
                log.error(
                    "Chimera is already running on this machine. Use chimera-admin to manage it."
                )
                sys.exit(1)

            log.info(
                "Chimera: running on "
                + self.manager.get_hostname()
                + ":"
                + str(self.manager.get_port())
            )
            log.info(
                f"Chimera: reading configuration from {os.path.realpath(self.options.config_file)}"
            )

        # add site object
        if not self.options.dry:

            for site in self.config.sites:
                self.manager.add_class(Site, site.name, site.config, True)

        # search paths
        log.info("Setting objects include path from command line parameters...")
        for _dir in self.options.inst_dir:
            self.paths["instruments"].append(_dir)

        for _dir in self.options.ctrl_dir:
            self.paths["controllers"].append(_dir)

        # init from config
        log.info("Trying to start instruments...")
        for inst in self.config.instruments + self.options.instruments:

            if self.options.dry:
                print(inst)
            else:
                self._add(inst, path=self.paths["instruments"], start=True)

        log.info("Trying to start controllers...")
        for ctrl in self.config.controllers + self.options.controllers:

            if self.options.dry:
                print(ctrl)
            else:
                self._add(ctrl, path=self.paths["controllers"], start=True)

        log.info("System up and running.")

        # ok, let's wait manager work
        if self.wait and not self.options.dry:
            self.manager.wait()

    def _add(self, location, path, start):
        try:
            self.manager.add_location(location, path, start)
        except Exception as e:
            print_exception(e)

    def shutdown(self):
        log.info("Shutting down system.")
        self.manager.shutdown()
