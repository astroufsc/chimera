import pytest

from chimera.controllers.ws.codegen import (
    _generated_files,
    extract_schema,
    render_schema,
)
from chimera.controllers.ws.introspect import describe_object, list_objects
from chimera.instruments.faketelescope import FakeTelescope


@pytest.mark.parametrize(
    "path", _generated_files(extract_schema()), ids=lambda p: p.name
)
def test_checked_in_generated_files_are_fresh(path):
    files = _generated_files(extract_schema())
    assert path.exists() and path.read_text() == files[path], (
        f"{path.name} is stale: run chimera-ws-codegen to regenerate"
    )


def test_schema_is_deterministic():
    assert render_schema(extract_schema()) == render_schema(extract_schema())


def test_telescope_slew_extraction():
    schema = extract_schema()
    slew = schema["interfaces"]["TelescopeSlew"]

    assert slew["bases"] == ["Telescope"]
    assert slew["module"] == "chimera.interfaces.telescope"

    params = slew["methods"]["slew_to_ra_dec"]["params"]
    assert [p["name"] for p in params] == ["ra", "dec", "epoch"]
    assert params[0]["type"] == {"kind": "float"}
    assert params[2]["default"] == 2000
    assert slew["methods"]["slew_to_ra_dec"]["returns"] == {"kind": "none"}

    status_param = slew["events"]["slew_complete"]["params"][2]
    assert status_param["type"] == {"kind": "enum", "enum": "TelescopeStatus"}
    assert schema["enums"]["TelescopeStatus"] == [
        "OK",
        "ERROR",
        "ABORTED",
        "OBJECT_TOO_LOW",
        "OBJECT_TOO_HIGH",
    ]


def test_enum_config_keeps_legal_values():
    schema = extract_schema()
    align = schema["interfaces"]["TelescopeSlew"]["config"]["align_mode"]
    assert align == {"type": {"kind": "enum", "enum": "AlignMode"}, "default": "POLAR"}
    assert schema["enums"]["AlignMode"] == ["ALT_AZ", "POLAR", "LAND"]


def test_variadic_params():
    expose = extract_schema()["interfaces"]["CameraExpose"]["methods"]["expose"]
    kwargs = expose["params"][-1]
    assert kwargs["variadic"] == "keyword"


def _fake_telescope_entry():
    return {
        "path": "/FakeTelescope/fake",
        "class": "FakeTelescope",
        "bases": [b.__name__ for b in FakeTelescope.mro()],
        "state": "State.RUNNING",
        "config": {"model": "Fake Telescopes Inc."},
    }


def test_describe_unions_over_mro():
    description = describe_object(_fake_telescope_entry(), extract_schema())

    # members contributed by different capability interfaces all present
    assert "slew_to_ra_dec" in description["methods"]  # TelescopeSlew
    assert "park" in description["methods"]  # TelescopePark
    assert "start_tracking" in description["methods"]  # TelescopeTracking
    assert "get_location" in description["methods"]  # ILifeCycle
    assert "slew_complete" in description["events"]
    assert "tracking_stopped" in description["events"]
    assert "align_mode" in description["config_schema"]

    # interfaces listed leaf-first, only schema-known names
    assert "TelescopeSlew" in description["interfaces"]
    assert "ChimeraObject" not in description["interfaces"]
    assert "FakeTelescope" not in description["interfaces"]

    # live values pass through untouched
    assert description["state"] == "State.RUNNING"
    assert description["config"] == {"model": "Fake Telescopes Inc."}


def test_list_objects_projection():
    status = {"objects": [_fake_telescope_entry() | {"loop": "running", "age": 1.0}]}
    objects = list_objects(status)
    assert objects == [_fake_telescope_entry()]
