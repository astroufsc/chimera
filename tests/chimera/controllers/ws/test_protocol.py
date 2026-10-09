import json

import msgspec
import pytest

from chimera.controllers.ws import protocol as ws


@pytest.mark.parametrize(
    "message",
    [
        ws.Hello(protocol=1),
        ws.Hello(protocol=1, auth=ws.AuthInfo(scheme="bearer", token="secret")),
        ws.Call(
            id="c1", path="/Telescope/0", method="slew_to_ra_dec", args=[10.5, -30.2]
        ),
        ws.Call(id="c2", path="/Telescope/0", method="get_ra", timeout=5.0),
        ws.Subscribe(id="c3", path="/Telescope/0", event="slew_complete"),
        ws.Unsubscribe(id="c4", path="/Telescope/0", event="slew_complete"),
        ws.ListObjects(id="c5"),
        ws.Describe(id="c6", path="/Telescope/0"),
        ws.GetSchema(id="c7"),
        ws.Ping(id="c8"),
    ],
)
def test_client_message_round_trip(message):
    assert ws.decode_client_message(ws.encode(message)) == message


@pytest.mark.parametrize(
    "message",
    [
        ws.Welcome(protocol=1, server={"chimera": "0.2"}),
        ws.Result(id="c1", value=[10.5, -30.2]),
        ws.Result(id="c1"),
        ws.Error(id="c1", code=ws.ERROR_BUSY, message="lane full"),
        ws.Error(id=None, code=ws.ERROR_PROTOCOL_ERROR, message="hello first"),
        ws.Event(
            path="/FakeTelescope/fake",
            event="slew_complete",
            args=[10.5, -30.2, "OK"],
            kwargs={},
            ts=1785000000000,
        ),
        ws.Pong(id="c8"),
    ],
)
def test_server_message_round_trip(message):
    assert ws.decode_server_message(ws.encode(message)) == message


@pytest.mark.parametrize(
    ("message", "tag"),
    [
        (ws.Hello(protocol=1), "hello"),
        (ws.ListObjects(id="c1"), "list"),
        (ws.GetSchema(id="c1"), "schema"),
        (ws.Ping(id="c1"), "ping"),
    ],
)
def test_wire_tag_is_lowercase_type_field(message, tag):
    assert json.loads(ws.encode(message))["type"] == tag


def test_unknown_type_rejected():
    with pytest.raises(msgspec.DecodeError):
        ws.decode_client_message(b'{"type": "explode", "id": "c1"}')


def test_garbage_rejected():
    with pytest.raises(msgspec.DecodeError):
        ws.decode_client_message(b"not json at all")


def test_missing_required_field_rejected():
    with pytest.raises(msgspec.DecodeError):
        ws.decode_client_message(b'{"type": "call", "id": "c1"}')


def test_call_defaults():
    call = ws.decode_client_message(
        b'{"type": "call", "id": "c1", "path": "/Telescope/0", "method": "get_ra"}'
    )
    assert call.args == [] and call.kwargs == {} and call.timeout is None
