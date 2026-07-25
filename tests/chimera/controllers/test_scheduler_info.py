import msgspec
import pytest

from chimera.controllers.scheduler.controller import action_info, program_info
from chimera.controllers.scheduler.model import (
    AutoFlat,
    AutoFocus,
    Autoguide,
    Expose,
    Operator,
    Point,
    PointVerify,
    Program,
)
from chimera.util.coord import Coord
from chimera.util.position import Position


def test_none_inputs():
    assert program_info(None) is None
    assert action_info(None) is None


def test_program_info_is_encodable():
    info = program_info(Program(name="Science", pi="pi", priority=10))
    assert info["name"] == "Science"
    decoded = msgspec.json.decode(msgspec.json.encode(info))
    assert decoded["pi"] == "pi"


@pytest.mark.parametrize(
    "action",
    [
        Expose(exptime=10, frames=2, image_type="OBJECT"),
        Point(target_ra_dec=Position.from_ra_dec("14:00:00", "-30:00:00")),
        Point(target_alt_az=Position.from_alt_az("80:00:00", "10:00:00")),
        Point(offset_ns=Coord.from_as(600), offset_ew=Coord.from_as(-300)),
        Point(),
        AutoFocus(start=100, end=200, step=10),
        AutoFlat(filter="B", frames=5),
        Autoguide(enable=True),
        Autoguide(enable=False),
        PointVerify(here=True),
        PointVerify(),
        Operator(type="confirm", message="go?"),
    ],
    ids=lambda action: str(action),
)
def test_action_info_is_encodable_for_every_action_type(action):
    info = action_info(action)
    assert info["type"] == type(action).__name__
    assert isinstance(info["description"], str)
    # the exact wire path: a plain msgspec encoder with no enc_hook — the
    # Point cases are the load-bearing ones (PickleType Coord/Position values)
    msgspec.json.encode(info)
