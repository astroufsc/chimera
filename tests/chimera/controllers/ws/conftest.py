import json
import random
import time

import pytest
from websockets.sync.client import connect

from chimera.controllers.ws.gateway import GatewayCore
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event
from chimera.core.url import create_url


class Thing(ChimeraObject):
    """A fast test object: instant methods, an event, a raiser, a sleeper."""

    def __init__(self):
        ChimeraObject.__init__(self)

    def echo(self, x):
        return x

    def boom(self):
        raise RuntimeError("kaboom")

    def nap(self, seconds: float) -> None:
        time.sleep(seconds)

    def fire(self, n: int) -> None:
        self.pinged(n)

    @event
    def pinged(self, n: int) -> None:
        pass


@pytest.fixture
def gateway(manager):
    manager.add_class(Thing, "thing")

    core = GatewayCore(
        bus=manager._bus,
        gateway_url=create_url(
            bus=manager._bus.url.bus, cls="WsGateway", name="test"
        ).url,
        manager_url=manager.get_location(),
        ws_host="127.0.0.1",
        ws_port=random.randint(20000, 60000),
        standalone=False,
    )
    core.start()
    yield core
    core.stop()


class WsClient:
    """A tiny synchronous test client speaking the WS envelope."""

    def __init__(self, url: str, hello: bool = True):
        self.ws = connect(url)
        self.events: list[dict] = []
        self._counter = 0
        if hello:
            self.send({"type": "hello", "protocol": 1})
            welcome = self.recv()
            assert welcome["type"] == "welcome", welcome

    def send(self, message: dict) -> None:
        self.ws.send(json.dumps(message))

    def recv(self, timeout: float = 10.0) -> dict:
        frame = self.ws.recv(timeout)
        # browsers surface BINARY frames as Blobs: the gateway must send TEXT
        assert isinstance(frame, str), f"expected a TEXT frame, got {type(frame)}"
        return json.loads(frame)

    def rpc(self, type_: str, recv_timeout: float = 10.0, **fields) -> dict:
        """Send a request, buffer events, return the matching result/error.

        Wire fields (including the call's own "timeout") go in **fields;
        recv_timeout only bounds how long we wait for the reply frame.
        """
        self._counter += 1
        id_ = f"c{self._counter}"
        self.send({"type": type_, "id": id_, **fields})
        deadline = time.monotonic() + recv_timeout
        while True:
            message = self.recv(timeout=max(0.05, deadline - time.monotonic()))
            if message["type"] == "event":
                self.events.append(message)
                continue
            assert message.get("id") == id_, message
            return message

    def wait_event(self, timeout: float = 10.0) -> dict:
        if self.events:
            return self.events.pop(0)
        return self.recv(timeout=timeout)

    def close(self) -> None:
        self.ws.close()


@pytest.fixture
def ws_client(gateway):
    clients = []

    def factory(hello: bool = True) -> WsClient:
        client = WsClient(f"ws://127.0.0.1:{gateway.ws_port}", hello=hello)
        clients.append(client)
        return client

    yield factory

    for client in clients:
        try:
            client.close()
        except Exception:
            pass
