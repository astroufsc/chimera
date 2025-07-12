import time

import pytest

from chimera.core.protocol import Protocol
from chimera.core.transport import Transport
from chimera.core.transport_factory import create_transport


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
    def test_ping(self, create_server, create_client):
        server: Transport = create_server("tcp://127.0.0.1:6379")
        server.bind()

        client: Transport = create_client("tcp://127.0.0.1:6379")
        client.connect()

        assert client.ping() is True

        client.close()
        del client

        server.close()
        del server

    def test_single_request_reply(self, create_server, create_client):
        server: Transport = create_server("tcp://127.0.0.1:6379")
        server.bind()

        client: Transport = create_client("tcp://127.0.0.1:6379")
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

        client.close()
        del client

        server.close()
        del server

    def test_multiple_queued_requests(self, create_server, create_client):
        server: Transport = create_server("tcp://127.0.0.1:6379")
        server.bind()

        client_1: Transport = create_client("tcp://127.0.0.1:6379")
        client_1.connect()
        client_1_request = Protocol().request(
            location="/Foo/bar",
            method="get_from_client_1",
            args=(1, 2),
            kwargs={"a": 3, "b": 4},
        )
        client_1.send_request(client_1_request)

        client_2: Transport = create_client("tcp://127.0.0.1:6379")
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

        client_1.close()
        del client_1

        client_2.close()
        del client_2

        server.close()
        del server

    def test_simple_pubsub(self, mocker, create_server, create_client):
        publisher: Transport = create_server("tcp://127.0.0.1:6379")
        publisher.bind()

        subscriber: Transport = create_client("tcp://127.0.0.1:6379")
        subscriber.connect()

        callback = mocker.MagicMock()
        subscriber.subscribe("test_topic", callback)

        test_topic_event = Protocol().event(
            location="test_topic",  # ?
            args=(42,),
            kwargs={"b": "something happened"},
        )

        publisher.publish("test_topic", test_topic_event)

        elapsed = 0.0
        while not callback.called and elapsed < 2.0:
            time.sleep(0.1)
            elapsed += 0.1

        callback.assert_called_once()
        callback.assert_called_with(42, b="something happened")

        subscriber.close()
        del subscriber

        publisher.close()
        del publisher

    def test_multiple_subscribers_pubsub(self, mocker, create_server, create_client):
        publisher: Transport = create_server("tcp://127.0.0.1:6379")
        publisher.bind()

        subscriber_1: Transport = create_client("tcp://127.0.0.1:6379")
        subscriber_1.connect()

        subscriber_2: Transport = create_client("tcp://127.0.0.1:6379")
        subscriber_2.connect()

        callback_1 = mocker.MagicMock()
        callback_2 = mocker.MagicMock()

        subscriber_1.subscribe("test_topic", callback_1)
        subscriber_2.subscribe("test_topic", callback_2)

        test_topic_event = Protocol().event(
            location="test_topic",  # ?
            args=(42,),
            kwargs={"b": "something happened"},
        )

        publisher.publish("test_topic", test_topic_event)

        elapsed = 0.0
        while not callback_1.called and not callback_2.called and elapsed < 2.0:
            time.sleep(0.1)
            elapsed += 0.1

        callback_1.assert_called_once()
        callback_1.assert_called_with(42, b="something happened")

        callback_2.assert_called_once()
        callback_2.assert_called_with(42, b="something happened")

        subscriber_1.close()
        subscriber_2.close()

        del subscriber_1
        del subscriber_2

        publisher.close()
        del publisher
