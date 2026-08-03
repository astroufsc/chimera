import json

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from chimera.instruments.faketelescope import FakeTelescope

#
# handshake
#


def test_hello_welcome(gateway, ws_client):
    client = ws_client(hello=False)
    client.send({"type": "hello", "protocol": 1})
    welcome = client.recv()
    assert welcome["type"] == "welcome"
    assert welcome["protocol"] == 1
    assert welcome["server"]["chimera"]
    assert welcome["auth"] == "none"


def test_non_hello_first_message_is_rejected(gateway, ws_client):
    client = ws_client(hello=False)
    client.send({"type": "ping", "id": "c1"})
    error = client.recv()
    assert error["type"] == "error" and error["code"] == "protocol_error"
    with pytest.raises(ConnectionClosed) as exc_info:
        client.recv()
    assert exc_info.value.rcvd.code == 4002


def test_unsupported_protocol_version_is_rejected(gateway, ws_client):
    client = ws_client(hello=False)
    client.send({"type": "hello", "protocol": 99})
    error = client.recv()
    assert error["type"] == "error" and error["code"] == "unsupported_protocol"
    with pytest.raises(ConnectionClosed) as exc_info:
        client.recv()
    assert exc_info.value.rcvd.code == 4001


def test_undecodable_first_frame_is_rejected(gateway):
    ws = connect(f"ws://127.0.0.1:{gateway.ws_port}")
    ws.send("this is not json")
    error = json.loads(ws.recv(10))
    assert error["type"] == "error" and error["code"] == "protocol_error"


def test_app_level_ping(gateway, ws_client):
    client = ws_client()
    assert client.rpc("ping")["type"] == "pong"


#
# discovery
#


def test_schema(gateway, ws_client):
    schema = ws_client().rpc("schema")["value"]
    assert "TelescopeSlew" in schema["interfaces"]
    assert "TelescopeStatus" in schema["enums"]


def test_list_objects(gateway, ws_client):
    objects = ws_client().rpc("list")["value"]
    thing = next(o for o in objects if o["path"] == "/Thing/thing")
    assert thing["class"] == "Thing"
    assert "ChimeraObject" in thing["bases"]
    assert thing["state"] is not None


def test_describe_resolves_index_paths(gateway, manager, ws_client):
    manager.add_class(FakeTelescope, "fake")
    description = ws_client().rpc("describe", path="/Telescope/0")["value"]
    assert description["path"] == "/FakeTelescope/fake"
    assert "slew_to_ra_dec" in description["methods"]
    assert "slew_complete" in description["events"]
    assert "TelescopeSlew" in description["interfaces"]
    assert "align_mode" in description["config_schema"]
    assert description["config"]["model"]


def test_describe_unknown_object(gateway, ws_client):
    error = ws_client().rpc("describe", path="/Missing/0")
    assert error["type"] == "error" and error["code"] == "not_found"


#
# calls
#


def test_call_round_trip(gateway, manager, ws_client):
    manager.add_class(FakeTelescope, "fake")
    client = ws_client()

    result = client.rpc("call", path="/Thing/thing", method="echo", args=[[1, "a"]])
    assert result["type"] == "result" and result["value"] == [1, "a"]

    position = client.rpc("call", path="/Telescope/0", method="get_position_ra_dec")
    assert isinstance(position["value"], list) and len(position["value"]) == 2


def test_call_unknown_path(gateway, ws_client):
    error = ws_client().rpc("call", path="/Missing/0", method="whatever")
    assert error["type"] == "error" and error["code"] == "not_found"


def test_call_invalid_path(gateway, ws_client):
    error = ws_client().rpc("call", path="not a path", method="whatever")
    assert error["type"] == "error" and error["code"] == "bad_request"


def test_call_unknown_method(gateway, ws_client):
    error = ws_client().rpc("call", path="/Thing/thing", method="explode")
    assert error["type"] == "error" and error["code"] == "not_found"


def test_call_raising_method_maps_to_remote_error(gateway, ws_client):
    error = ws_client().rpc("call", path="/Thing/thing", method="boom")
    assert error["type"] == "error" and error["code"] == "remote_error"
    assert "kaboom" in error["message"]


def test_call_timeout_only_abandons_the_wait(gateway, ws_client):
    error = ws_client().rpc(
        "call", path="/Thing/thing", method="nap", args=[0.5], timeout=0.05
    )
    assert error["type"] == "error" and error["code"] == "timeout"


#
# events
#


def test_subscribe_and_receive_event(gateway, ws_client):
    client = ws_client()
    subscription = client.rpc("subscribe", path="/Thing/thing", event="pinged")
    assert subscription["value"] == {"path": "/Thing/thing", "event": "pinged"}

    client.rpc("call", path="/Thing/thing", method="fire", args=[7])
    event = client.wait_event()
    assert event["path"] == "/Thing/thing"
    assert event["event"] == "pinged"
    assert event["args"] == [7]
    assert event["ts"] > 0


def test_unsubscribe_stops_delivery(gateway, ws_client):
    client = ws_client()
    client.rpc("subscribe", path="/Thing/thing", event="pinged")
    client.rpc("unsubscribe", path="/Thing/thing", event="pinged")
    client.rpc("call", path="/Thing/thing", method="fire", args=[1])
    with pytest.raises(TimeoutError):
        client.wait_event(timeout=0.5)


def test_fanout_and_refcounting(gateway, ws_client, wait_for):
    first = ws_client()
    second = ws_client()
    first.rpc("subscribe", path="/Thing/thing", event="pinged")
    second.rpc("subscribe", path="/Thing/thing", event="pinged")

    first.rpc("call", path="/Thing/thing", method="fire", args=[1])
    assert first.wait_event()["args"] == [1]
    assert second.wait_event()["args"] == [1]

    # closing one consumer must not tear down the shared bus subscription
    first.close()
    assert wait_for(lambda: sum(gateway.broker.stats().values()) == 1)
    second.rpc("call", path="/Thing/thing", method="fire", args=[2])
    assert second.wait_event()["args"] == [2]


def test_abrupt_close_releases_subscriptions(gateway, ws_client, wait_for):
    client = ws_client()
    client.rpc("subscribe", path="/Thing/thing", event="pinged")
    assert gateway.broker.stats()
    client.close()
    assert wait_for(lambda: not gateway.broker.stats())
