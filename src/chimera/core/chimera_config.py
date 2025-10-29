#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import logging
from collections.abc import Callable
from typing import Any

import msgspec

from chimera.core.constants import (
    CHIMERA_CONFIG_DEFAULT_FILENAME,
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
)
from chimera.core.url import URL, parse_url

log = logging.getLogger(__name__)


class ChimeraConfig:
    """

    Chimera configuration system
    ============================

    Chimera uses YAML format for its configuration system. YAML uses
    basic syntax to allow sequences and maps to be easily parsed.

    A map (a key=value sequence) is defined using:
     key: value
     otherkey: value

    will be mapped to {'key': 'value', 'otherkey': 'value'}

    A sequence is defined as (in this case a simple progression)
    - 1
    - 2
    - 3

    will be mapped to [1,2,3]

    Chimera uses both maps and sequences. It use keys that maps to
    Instrmuments/Controllers names. And for each key, the value can be
    either another map or a sequence of maps.

    The following example defines a instrument with a few parameters:

     instrument:
      parameter_1: value1
      parameter_2: value2
      parameter_3: value3

    To define more than one instance, just pass a sequence as the
    maps value, as in:

     instrument:
     - parameter_1: value1
       parameter_2: value2
       parameter_3: value3

     - parameter_1: other1
       parameter_2: other2
       parameter_3: other3

    You could also pass another map as a parameter value, as in:

     instrument:
      parameter_1:
        parameterkey: paramatervalue

    this would be mapped to:

    {'InstrumentType': {'parameter1': {'parameterkey': 'parametervalue'}

    Chimera accepts definition of instruments and controllers. Besides
    this, there are specials shortcut to most common object types
    (like telescopes).

    For each object, Chimera accepts a set os parameters plus any
    other parameter specific to the given object type. The deault
    parameters are:

    name: a_valid_chimera_name_for_the_instance
    type: ChimeraObject type
    host: where this object is/or will be located.
    port: port where to find the object on the given host

    For special shortcuts the type would be guessed, so the folling
    two entries are equivalent:

    instrument:
     type: Telescope
     name: meade
     device: /dev/ttyS0

    telescope:
     name: meade
     device: /dev/ttyS0
    """

    @staticmethod
    def from_file(filename: str):
        if filename.endswith(".toml"):
            decode = msgspec.toml.decode
        elif filename.endswith(".config"):
            decode = msgspec.yaml.decode
        else:
            raise ValueError(
                "Unsupported configuration file format.Only YAML and TOML are supported."
            )

        return ChimeraConfig(open(filename).read(), decoder=decode)

    @staticmethod
    def from_default():
        return ChimeraConfig.from_file(CHIMERA_CONFIG_DEFAULT_FILENAME)

    def __init__(self, /, text: str, decoder: Callable[[str], Any]):
        self.sites: dict[URL, Any] = {}
        self.instruments: dict[URL, Any] = {}
        self.controllers: dict[URL, Any] = {}

        self.host = MANAGER_DEFAULT_HOST
        self.port = MANAGER_DEFAULT_PORT

        self._parse(text, decoder)

    def _parse(self, text: str, decoder: Callable[[str], Any]):
        config: dict[str, dict[str, Any] | list[dict[str, Any]]] = decoder(text)

        chimera_config = config.pop("chimera", {})
        # FIXME: raise and let user fix it
        assert isinstance(chimera_config, dict)

        self.host = chimera_config.get("host", MANAGER_DEFAULT_HOST)
        self.port = chimera_config.get("port", MANAGER_DEFAULT_PORT)

        site_config = config.pop("site", {})
        # FIXME: raise and let user fix it
        assert isinstance(site_config, dict)

        site_config["type"] = "Site"
        site_url, site_conf = self._parse_config(site_config)
        self.sites[site_url] = site_conf

        for type, object_configs in config.items():
            # NOTE: this allow both toml and yaml to coexist
            if not isinstance(object_configs, list):
                object_configs = [object_configs]

            for object_config in object_configs:
                url, conf = self._parse_config(object_config)
                match type.lower():
                    case "controller" | "controllers":
                        self.controllers[url] = conf
                    case _:
                        self.instruments[url] = conf

    def _parse_config(self, config: dict[str, Any]) -> tuple[URL, dict[str, Any]]:
        host = config.pop("host", self.host)
        port = config.pop("port", self.port)
        cls = config.pop("type")
        name = config.pop("name")

        # # FIXME: raise and let user fix it
        # name = name.replace(" ", "_")
        # name = name.replace('"', "_")
        # name = name.replace("'", "_")

        url = parse_url(f"tcp://{host}:{port}/{cls}/{name}")
        return url, config
