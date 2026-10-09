import random
import threading

import pytest

from chimera.controllers.ws.gateway import GatewayCore
from chimera.controllers.wsgateway import WsGateway
from chimera.core.bus import Bus
from chimera.core.url import create_url
from chimera.instruments.faketelescope import FakeTelescope

from .conftest import Thing, WsClient


def test_controller_shell(manager):
    """WsGateway as a managed controller: start via add_class, serve, stop."""
    port = random.randint(20000, 60000)
    manager.add_class(WsGateway, "ws", {"ws_host": "127.0.0.1", "ws_port": port})

    client = WsClient(f"ws://127.0.0.1:{port}")
    try:
        objects = client.rpc("list")["value"]
        assert any(o["path"] == "/WsGateway/ws" for o in objects)
        pong = client.rpc("ping")
        assert pong["type"] == "pong"
    finally:
        client.close()


@pytest.fixture
def standalone_gateway(manager):
    """A GatewayCore on its OWN bus, peering with the manager's bus over NNG
    — the chimera-ws process shape, in-process."""
    manager.add_class(Thing, "thing")

    bus = Bus(f"tcp://127.0.0.1:{random.randint(20000, 60000)}")
    bus_thread = threading.Thread(target=bus.run_forever, daemon=True)
    bus_thread.start()
    assert bus._bus_started.wait(5)

    core = GatewayCore(
        bus=bus,
        gateway_url=create_url(bus=bus.url.bus, cls="WsGateway", name="ws").url,
        manager_url=manager.get_location(),
        ws_host="127.0.0.1",
        ws_port=random.randint(20000, 60000),
        standalone=True,
    )
    core.start()
    yield core
    core.stop()
    bus.shutdown()
    bus_thread.join(timeout=10)


def test_standalone_cross_bus(standalone_gateway, wait_for):
    """Calls and events cross two real buses: browser -> gateway bus -> server
    bus and back."""
    client = WsClient(f"ws://127.0.0.1:{standalone_gateway.ws_port}")
    try:
        result = client.rpc("call", path="/Thing/thing", method="echo", args=[42])
        assert result["value"] == 42

        client.rpc("subscribe", path="/Thing/thing", event="pinged")
        client.rpc("call", path="/Thing/thing", method="fire", args=[9])
        event = client.wait_event()
        assert event["event"] == "pinged" and event["args"] == [9]
    finally:
        client.close()


@pytest.mark.slow
def test_faketelescope_slew_end_to_end(gateway, manager, ws_client):
    """The real thing: slew a FakeTelescope from a WS client and watch
    slew_begin/slew_complete arrive (~5 s of simulated slewing)."""
    manager.add_class(FakeTelescope, "fake")
    client = ws_client()

    # park at a high altitude first so the ra/dec slew stays above the
    # minimum-altitude limit (same dance as tests/chimera/instruments);
    # slew_to_alt_az is @lock, so this also exercises the lane path over WS
    result = client.rpc(
        "call",
        path="/Telescope/0",
        method="slew_to_alt_az",
        args=[60.0, 30.0],
        recv_timeout=30.0,
    )
    assert result["type"] == "result"
    ra, dec = client.rpc("call", path="/Telescope/0", method="get_position_ra_dec")[
        "value"
    ]

    client.rpc("subscribe", path="/Telescope/0", event="slew_begin")
    client.rpc("subscribe", path="/Telescope/0", event="slew_complete")

    result = client.rpc(
        "call",
        path="/Telescope/0",
        method="slew_to_ra_dec",
        args=[ra + 0.5, dec + 2],
        recv_timeout=30.0,
    )
    assert result["type"] == "result"

    events = [client.wait_event(), client.wait_event()]
    names = {e["event"] for e in events}
    assert names == {"slew_begin", "slew_complete"}
    for e in events:
        assert e["path"] == "/FakeTelescope/fake"

    complete = next(e for e in events if e["event"] == "slew_complete")
    ra, dec, status = complete["args"]
    assert status == "OK"
    assert isinstance(ra, float) and isinstance(dec, float)
