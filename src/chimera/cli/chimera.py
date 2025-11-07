#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import argparse
import logging
import os.path
import platform
import sys
from typing import Any

import chimera.core.log
from chimera.core.bus import Bus
from chimera.core.chimera_config import ChimeraConfig
from chimera.core.constants import CHIMERA_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import ChimeraException
from chimera.core.manager import Manager
from chimera.core.path import ChimeraPath
from chimera.core.site import Site
from chimera.core.url import URL
from chimera.core.version import chimera_version

log = logging.getLogger(__name__)


class ChimeraCLI:
    def __init__(self):
        self.options = self.parse_args()

        try:
            self.config = ChimeraConfig.from_file(self.options.config_file)
        except OSError as e:
            log.exception(e)
            log.error(f"There was a problem reading your configuration file. ({e})")
            sys.exit(1)

        if self.options.verbose == 0:
            chimera.core.log.set_console_level(logging.WARNING)
        elif self.options.verbose == 1:
            chimera.core.log.set_console_level(logging.INFO)
        elif self.options.verbose >= 2:
            chimera.core.log.set_console_level(logging.DEBUG)

        if self.options.host is None:
            self.options.host = self.config.host

        if self.options.port is None:
            self.options.port = self.config.port

        self.paths = ChimeraPath()

    def parse_args(self):
        parser = argparse.ArgumentParser(
            prog="chimera",
            usage="chimera --help for more information",
        )
        parser.add_argument("--version", action="version", version=chimera_version)

        bus_group = parser.add_argument_group("bus configuration")
        bus_group.add_argument(
            "-H",
            "--host",
            action="store",
            dest="host",
            type=str,
            help="Host name/IP address to run as; [default=%(default)s]",
            metavar="HOST",
        )

        bus_group.add_argument(
            "-P",
            "--port",
            action="store",
            dest="port",
            type=int,
            help="Port on which to listen for requests; [default=%(default)s]",
            metavar="PORT",
        )

        config_group = parser.add_argument_group("config")

        config_group.add_argument(
            "--config",
            dest="config_file",
            default=CHIMERA_CONFIG_DEFAULT_FILENAME,
            help="Start Chimera using configuration from FILE.",
            metavar="FILE",
        )

        misc_group = parser.add_argument_group("general")
        misc_group.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            dest="verbose",
            help="Increase log level (multiple v's to increase even more).",
        )

        return parser.parse_args()

    def run(self):
        log.info("Starting system.")
        log.info(f"Chimera version: {chimera_version}")
        log.info(f"Chimera config: {os.path.realpath(self.options.config_file)}")
        log.info(f"Chimera prefix: {ChimeraPath().root()}")
        log.info(f"Python: {platform.python_version()}")
        log.info(f"System: {platform.uname()}")

        try:
            self.bus = Bus(f"tcp://{self.options.host}:{self.options.port}")
            self.manager = Manager(bus=self.bus)
        except ChimeraException:
            log.error(
                "Chimera is already running on this machine. Use chimera-admin to manage it."
            )
            sys.exit(1)

        log.info(f"Chimera: running on {self.options.host}:{self.options.port}")

        # add site object
        for url, config in self.config.sites.items():
            self.manager.add_class(Site, url.name, config, start=True)

        # init from config
        log.info("Starting instruments...")
        for url, config in self.config.instruments.items():
            self._add(url, path=self.paths.instruments, start=True, config=config)
        log.info("Instruments started...")

        log.info("Starting controllers...")
        for url, config in self.config.controllers.items():
            self._add(url, path=self.paths.controllers, start=True, config=config)
        log.info("Controllers started...")

        log.info("System up and running.")

        try:
            self.bus.run_forever()
        except KeyboardInterrupt:
            log.info("Caught Ctrl-C, shutting down...")
        finally:
            self.shutdown()

    def _add(self, location: URL, path: list[str], start: bool, config: dict[str, Any]):
        try:
            self.manager.add_location(
                location,
                path=path,
                config=config,
                start=start,
            )
        except Exception:
            log.exception(f"error starting {location.path}")

    def shutdown(self):
        log.info("Shutting down system.")
        self.bus.shutdown()
        self.manager.shutdown()


def main():
    cli = ChimeraCLI()
    cli.run()


if __name__ == "__main__":
    main()
