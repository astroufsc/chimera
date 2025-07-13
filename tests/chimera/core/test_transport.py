from chimera.core.protocol import Protocol
from chimera.core.transport import Transport
from chimera.core.transport_factory import create_transport

import pytest


@pytest.fixture
def create_server():
    servers = []

    def _(url: str):
        server = create_transport(url)
        servers.append(server)
        return server

    yield _

    for server in servers:
        server.close()


@pytest.fixture
def create_client():
    clients = []

    def _(url: str):
        client = create_transport(url)
        clients.append(client)
        return client

    yield _

    for client in clients:
        client.close()


class TestTransport:

    @pytest.mark.parametrize("transport", ["nng", "redis"])
    def test_single_request_reply(self, transport: str, create_server, create_client):
        server = create_server(f"{transport}://127.0.0.1:9000")
        server.bind()

        client = create_client(f"{transport}://127.0.0.1:9000")
        client.connect()

        client_request = Protocol().request(
            location="/Foo/bar",
            method="get_foobar",
            args=(1, 2),
            kwargs={"a": 3, "b": 4},
        )

        client.send_request(client_request)

        server_request = server.recv_request()
        assert server_request is not None

        server.send_response(server_request, Protocol().ok(42))

        client_response = client.recv_response(client_request)
        assert client_response is not None
        assert client_response.result == 42

    @pytest.mark.parametrize("transport", ["nng", "redis"])
    def test_multiple_queued_requests(
        self, transport: str, create_server, create_client
    ):
        server: Transport = create_server(f"{transport}://127.0.0.1:9000")
        server.bind()

        client_1: Transport = create_client(f"{transport}://127.0.0.1:9000")
        client_1.connect()
        client_1_request = Protocol().request(
            location="/Foo/bar",
            method="get_from_client_1",
            args=(1, 2),
            kwargs={"a": 3, "b": 4},
        )
        client_1.send_request(client_1_request)

        client_2: Transport = create_client(f"{transport}://127.0.0.1:9000")
        client_2.connect()
        client_2_request = Protocol().request(
            location="/Foo/bar",
            method="get_from_client_2",
            args=(4, 3),
            kwargs={"a": 2, "b": 1},
        )
        client_2.send_request(client_2_request)

        server_request_1 = server.recv_request()
        assert server_request_1 is not None

        server_request_2 = server.recv_request()
        assert server_request_2 is not None

        server.send_response(server_request_1, Protocol().ok(42))
        server.send_response(server_request_2, Protocol().ok(43))

        client_1_response = client_1.recv_response(client_1_request)
        assert client_1_response is not None
        assert client_1_response.result == 42

        client_2_response = client_2.recv_response(client_2_request)
        assert client_2_response is not None
        assert client_2_response.result == 43
