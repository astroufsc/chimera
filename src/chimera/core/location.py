# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: Copyright 2006-2024 Paulo Henrique Silva <ph.silva@gmail.com>

import re
import sys

from chimera.core.exceptions import InvalidLocationException

import logging

log = logging.getLogger(__name__)


class Location(object):
    """
    Location represents a specific resource available on the system.
    This location is the resource address on the system.

    Location objects are immutable, so please, respect this or hash operations
    will fail.
    """

    if sys.version_info[0:2] >= (2, 5):
        _re = re.compile(
            r"^(?P<host>[\w.]+)?(?(host)(?P<sep>:))?(?(sep)(?P<port>[\d]+))/+(?P<class>[\w]*)/+(?P<name>[\w]*)(?P<sep2>\??)?(?(sep2)(?P<config>[\w\S\s=,]*))"
        )
    else:
        _re = re.compile(
            r"^(?P<host>[\w.]+)?(?P<port>:[\d]+)?/+(?P<class>[\w]*)/+(?P<name>[\w]*)(?P<config>\?[\w\S\s=,]+)?"
        )

    def __init__(self, location=None, **options):

        self._host = None
        self._port = None
        self._class = None
        self._name = None
        self._config = None

        # simple string
        if isinstance(location, str):
            (self._host, self._port, self._class, self._name, self._config) = (
                self.parse(location)
            )
            if not self._host and "host" in options:
                if options["host"]:
                    self._host = options["host"]
            if not self._port and "port" in options:
                if options["port"]:
                    self._port = options["port"]

        # copy constructor
        elif isinstance(location, Location):
            self._host = location.host
            self._port = location.port
            self._class = location.cls
            self._name = location.name
            self._config = location.config

        # from dict
        else:
            # get from options dict (cls, name, config)
            loc = "/{}/{}".format(options.get("cls", ""), options.get("name", ""))

            _, __, self._class, self._name, ___ = self.parse(loc)

            self._config = options.get("config", {})
            self._host = options.get("host", None)
            self._port = options.get("port", None)

            if self._port:
                try:
                    self._port = int(self._port)
                except ValueError:
                    raise InvalidLocationException(
                        "Invalid location, port should be an "
                        f"integer not a {type(self._port)} ({self._port})."
                    )

    host = property(lambda self: self._host)
    port = property(lambda self: self._port)
    cls = property(lambda self: self._class)
    name = property(lambda self: self._name)
    config = property(lambda self: self._config)

    def parse(self, location):

        m = self._re.search(location)

        if not m:
            raise InvalidLocationException(
                f"Cannot parse '{location}' as a valid location."
            )

        matches = m.groupdict()

        conf = {}

        if matches["config"]:

            # FIXME? py2.4 hack
            if matches["config"][0] == "?":
                matches["config"] = matches["config"][1:]

            for opt in matches["config"].split(","):
                try:
                    k, v = opt.split("=")
                    conf[k.strip()] = v.strip()
                except ValueError:
                    # split returned less/more than 2 strings
                    raise InvalidLocationException(
                        "Cannot parse '{}' as a valid location. "
                        "Invalid config dict: '{}'".format(location, matches["config"])
                    )

        port = matches["port"]
        if port:
            # don't expect ValueError because RE already check this
            port = int(port)

        if not matches["name"]:
            raise InvalidLocationException("Invalid location name (must be non-blank).")

        if not matches["class"]:
            raise InvalidLocationException(
                "Invalid location class name (must be non-blank)."
            )

        return matches["host"], port, matches["class"], matches["name"], conf

    def __eq__(self, loc):

        if not isinstance(loc, Location):
            loc = Location(loc)

        return (loc.cls.lower() == self.cls.lower()) and (loc.name == self.name)

    def __ne__(self, loc):
        return not self.__eq__(loc)

    def __hash__(self):
        return hash(self.cls) ^ hash(self.name)

    def __repr__(self):

        _str = f"/{self._class}/{self._name}"

        if self.host and self.port:
            _str = f"{self.host}:{self.port}{_str}"

        if self.host and not self.port:
            _str = f"{self.host}{_str}"

        return _str
