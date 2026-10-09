# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""Extract a machine-readable schema of every chimera interface.

The schema drives three consumers: the gateway's "schema"/"describe"
messages, the generated TypeScript types (ts/src/generated/), and the web
UI's auto-built method forms. It is checked in next to this module and a
test regenerates it to catch drift when interfaces change.

Interfaces are introspected statically: MetaObject keeps the original
function (with annotations, defaults and docstring) at each wrapper's
.func, and stores per-class __methods__/__events__ lists. Each schema entry
describes only the members a class declares itself, plus its interface
bases — consumers merge over an object's MRO (see introspect.py).
"""

import argparse
import importlib
import inspect
import json
import pkgutil
from pathlib import Path
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin

import chimera.interfaces
from chimera.core.constants import (
    CONFIG_ATTRIBUTE_NAME,
    EVENTS_ATTRIBUTE_NAME,
    METHODS_ATTRIBUTE_NAME,
)
from chimera.core.interface import Interface
from chimera.util.enum import Enum

SCHEMA_VERSION = 1
SCHEMA_PATH = Path(__file__).with_name("schema.json")

type Enums = dict[str, list[str]]


def _iter_interface_classes():
    for modinfo in sorted(
        pkgutil.iter_modules(chimera.interfaces.__path__), key=lambda m: m.name
    ):
        module = importlib.import_module(f"chimera.interfaces.{modinfo.name}")
        for name, obj in sorted(vars(module).items()):
            if (
                isinstance(obj, type)
                and issubclass(obj, Interface)
                and obj is not Interface
                and obj.__module__ == module.__name__
            ):
                yield name, obj


def _type_descriptor(annotation: Any, enums: Enums) -> dict:
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {"kind": "any"}

    if annotation is None or annotation is NoneType:
        return {"kind": "none"}

    if isinstance(annotation, type):
        if issubclass(annotation, Enum):
            enums[annotation.__name__] = [member.value for member in annotation]
            return {"kind": "enum", "enum": annotation.__name__}
        if annotation is bool:
            return {"kind": "bool"}
        if annotation is int:
            return {"kind": "int"}
        if annotation is float:
            return {"kind": "float"}
        if annotation is str:
            return {"kind": "str"}
        if annotation is dict:
            return {"kind": "dict", "value": {"kind": "any"}}
        if annotation is list:
            return {"kind": "list", "item": {"kind": "any"}}

    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        return {
            "kind": "union",
            "options": [_type_descriptor(a, enums) for a in get_args(annotation)],
        }
    if origin is tuple:
        return {
            "kind": "tuple",
            "items": [_type_descriptor(a, enums) for a in get_args(annotation)],
        }
    if origin is list:
        args = get_args(annotation)
        item = _type_descriptor(args[0], enums) if args else {"kind": "any"}
        return {"kind": "list", "item": item}
    if origin is dict:
        args = get_args(annotation)
        value = _type_descriptor(args[1], enums) if len(args) == 2 else {"kind": "any"}
        return {"kind": "dict", "value": value}

    return {"kind": "any"}


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_json_default(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _config_entry(default: Any, enums: Enums) -> dict:
    # mirrors the dispatch in chimera.core.config.Config._read_options,
    # except that Enum is tested before str (StrEnum members *are* str, and
    # we want the legal-values list, which Config itself loses)
    if isinstance(default, bool):
        return {"type": {"kind": "bool"}, "default": default}
    if isinstance(default, Enum):
        return {
            "type": _type_descriptor(type(default), enums),
            "default": default.value,
        }
    if isinstance(default, int):
        return {"type": {"kind": "int"}, "default": default}
    if isinstance(default, float):
        return {"type": {"kind": "float"}, "default": default}
    if isinstance(default, str):
        return {"type": {"kind": "str"}, "default": default}
    if default is None:
        return {"type": {"kind": "any"}, "default": None}
    if isinstance(default, dict):
        return {"type": {"kind": "dict", "value": {"kind": "any"}}, "default": default}
    # config conventions: a non-empty list enumerates the legal choices with
    # the first as default; a non-empty tuple is an inclusive (min, max)
    # range with the min as default; empty ones mean "anything, default None"
    if isinstance(default, list):
        if not default:
            return {"type": {"kind": "any"}, "default": None}
        entry = _config_entry(default[0], enums)
        entry["choices"] = [_json_default(v) for v in default]
        return entry
    if isinstance(default, tuple):
        if not default:
            return {"type": {"kind": "any"}, "default": None}
        entry = _config_entry(default[0], enums)
        entry["range"] = [_json_default(v) for v in default]
        return entry
    return {"type": {"kind": "any"}, "default": _json_default(default)}


def _doc(obj: Any) -> str | None:
    return inspect.cleandoc(obj.__doc__) if obj.__doc__ else None


def _params(func, enums: Enums) -> list[dict]:
    params = []
    for param in list(inspect.signature(func).parameters.values())[1:]:  # skip self
        entry: dict[str, Any] = {
            "name": param.name,
            "type": _type_descriptor(param.annotation, enums),
        }
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            entry["variadic"] = "positional"
        elif param.kind is inspect.Parameter.VAR_KEYWORD:
            entry["variadic"] = "keyword"
        if param.default is not inspect.Parameter.empty:
            entry["default"] = _json_default(param.default)
        params.append(entry)
    return params


def _describe_interface(cls: type, enums: Enums) -> dict:
    methods = {}
    for name in sorted(cls.__dict__.get(METHODS_ATTRIBUTE_NAME, [])):
        func = cls.__dict__[name].func
        signature = inspect.signature(func)
        methods[name] = {
            "doc": _doc(func),
            "params": _params(func, enums),
            "returns": _type_descriptor(
                signature.return_annotation
                if signature.return_annotation is not inspect.Signature.empty
                else inspect.Parameter.empty,
                enums,
            ),
        }

    events = {}
    for name in sorted(cls.__dict__.get(EVENTS_ATTRIBUTE_NAME, [])):
        func = cls.__dict__[name].func
        events[name] = {"doc": _doc(func), "params": _params(func, enums)}

    return {
        "module": cls.__module__,
        "bases": [
            b.__name__
            for b in cls.__bases__
            if b is not Interface and issubclass(b, Interface)
        ],
        "doc": _doc(cls),
        # __config__ on the class is already MRO-merged by MetaObject; TS
        # config types are emitted standalone (no extends) for that reason
        "config": {
            name: _config_entry(default, enums)
            for name, default in sorted(cls.__dict__[CONFIG_ATTRIBUTE_NAME].items())
        },
        "methods": methods,
        "events": events,
    }


def extract_schema() -> dict:
    enums: Enums = {}
    interfaces = {}
    for name, cls in _iter_interface_classes():
        interfaces[name] = _describe_interface(cls, enums)
    return {"version": SCHEMA_VERSION, "enums": enums, "interfaces": interfaces}


def render_schema(schema: dict) -> str:
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


#
# TypeScript emission (ts/src/generated/)
#

TS_GENERATED_DIR = Path(__file__).with_name("ts") / "src" / "generated"
TS_HEADER = "// generated by chimera-ws-codegen — do not edit\n\n"


def _ts_type(descriptor: dict, position: str = "value") -> str:
    match descriptor["kind"]:
        case "any":
            return "unknown"
        case "none":
            return "void" if position == "return" else "null"
        case "int" | "float":
            return "number"
        case "str":
            return "string"
        case "bool":
            return "boolean"
        case "enum":
            return descriptor["enum"]
        case "tuple":
            items = ", ".join(_ts_type(i) for i in descriptor["items"])
            return f"[{items}]"
        case "list":
            return f"{_ts_type(descriptor['item'])}[]"
        case "dict":
            return f"Record<string, {_ts_type(descriptor['value'])}>"
        case "union":
            return " | ".join(_ts_type(o) for o in descriptor["options"])
    return "unknown"


def _ts_params(params: list[dict]) -> str:
    parts = []
    optional = False  # once one param is optional, all following must be
    for param in params:
        if param.get("variadic") == "positional":
            parts.append("...args: unknown[]")
            continue
        if param.get("variadic") == "keyword":
            parts.append("kwargs?: Record<string, unknown>")
            continue
        optional = optional or "default" in param
        marker = "?" if optional else ""
        parts.append(f"{param['name']}{marker}: {_ts_type(param['type'])}")
    return ", ".join(parts)


def _ts_doc(doc: str | None, indent: str = "  ") -> str:
    if not doc:
        return ""
    body = doc.replace("*/", "*\\/")
    lines = [f"{indent}/**"]
    lines += [f"{indent} * {line}".rstrip() for line in body.splitlines()]
    lines.append(f"{indent} */")
    return "\n".join(lines) + "\n"


def render_ts_enums(schema: dict) -> str:
    out = [TS_HEADER]
    for name, members in sorted(schema["enums"].items()):
        union = " | ".join(f'"{m}"' for m in members)
        entries = "\n".join(f'  {m}: "{m}",' for m in members)
        out.append(f"export type {name} = {union};\n")
        out.append(f"export const {name} = {{\n{entries}\n}} as const;\n\n")
    return "".join(out).rstrip() + "\n"


def render_ts_interfaces(schema: dict) -> str:
    enums_used = sorted(schema["enums"])
    out = [TS_HEADER]
    if enums_used:
        out.append(f"import type {{ {', '.join(enums_used)} }} from './enums.js';\n\n")

    for name, interface in sorted(schema["interfaces"].items()):
        bases = interface["bases"]

        extends = f" extends {', '.join(bases)}" if bases else ""
        out.append(_ts_doc(interface["doc"], indent=""))
        out.append(f"export interface {name}{extends} {{\n")
        for method_name, method in interface["methods"].items():
            out.append(_ts_doc(method["doc"]))
            returns = _ts_type(method["returns"], position="return")
            out.append(
                f"  {method_name}({_ts_params(method['params'])}): "
                f"Promise<{returns}>;\n"
            )
        out.append("}\n\n")

        events_extends = (
            f" extends {', '.join(f'{b}Events' for b in bases)}" if bases else ""
        )
        out.append(f"export interface {name}Events{events_extends} {{\n")
        for event_name, event in interface["events"].items():
            out.append(_ts_doc(event["doc"]))
            out.append(f"  {event_name}: ({_ts_params(event['params'])}) => void;\n")
        out.append("}\n\n")

        # config is MRO-merged on the python side already: standalone type
        out.append(f"export interface {name}Config {{\n")
        for option, entry in interface["config"].items():
            out.append(f"  {option}: {_ts_type(entry['type'])} | null;\n")
        out.append("}\n\n")

    return "".join(out).rstrip() + "\n"


def render_ts_schema(schema: dict) -> str:
    body = json.dumps(schema, indent=2, sort_keys=True)
    return f"{TS_HEADER}export const schema = {body} as const;\n"


def _generated_files(schema: dict) -> dict[Path, str]:
    return {
        SCHEMA_PATH: render_schema(schema),
        TS_GENERATED_DIR / "enums.ts": render_ts_enums(schema),
        TS_GENERATED_DIR / "interfaces.ts": render_ts_interfaces(schema),
        TS_GENERATED_DIR / "schema.ts": render_ts_schema(schema),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the WS gateway interface schema "
        "and TypeScript client types"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated files are up to date; exit 1 if stale",
    )
    args = parser.parse_args()

    files = _generated_files(extract_schema())

    if args.check:
        stale = [
            path
            for path, text in files.items()
            if not path.exists() or path.read_text() != text
        ]
        if stale:
            for path in stale:
                print(f"{path} is stale")
            print("run chimera-ws-codegen to regenerate")
            return 1
        print("generated files are up to date")
        return 0

    TS_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for path, text in files.items():
        path.write_text(text)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
