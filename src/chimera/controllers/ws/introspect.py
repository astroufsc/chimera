# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""Build the gateway's list/describe answers.

Pure functions over two inputs: the manager's get_status() snapshot (which
carries each object's MRO class names in "bases") and the static interface
schema (schema.json). Live reflection over the bus can't enumerate an
object's full surface — __methods__/__events__ are per-class lists — so
describe unions the schema entries of every interface in the object's MRO.
"""

import functools
import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).with_name("schema.json")


@functools.cache
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def list_objects(status: dict) -> list[dict]:
    return [
        {
            "path": entry["path"],
            "class": entry["class"],
            "bases": entry["bases"],
            "state": entry["state"],
            "config": entry["config"],
        }
        for entry in status["objects"]
    ]


def describe_object(entry: dict, schema: dict | None = None) -> dict[str, Any]:
    schema = schema or load_schema()

    # entry["bases"] is the MRO leaf-first; merge base-first so that a class
    # redeclaring a member overrides its ancestors
    interfaces = [b for b in entry["bases"] if b in schema["interfaces"]]

    methods: dict[str, Any] = {}
    events: dict[str, Any] = {}
    config_schema: dict[str, Any] = {}
    for name in reversed(interfaces):
        interface = schema["interfaces"][name]
        methods.update(interface["methods"])
        events.update(interface["events"])
        config_schema.update(interface["config"])

    return {
        "path": entry["path"],
        "class": entry["class"],
        "bases": entry["bases"],
        "state": entry["state"],
        "config": entry["config"],
        "interfaces": interfaces,
        "methods": methods,
        "events": events,
        "config_schema": config_schema,
        # member lists for every enum referenced by the descriptors above,
        # so UIs can render dropdowns without fetching the full schema
        "enums": schema["enums"],
    }
