from chimera.core.transport_nng import TransportNNG
from chimera.core.transport_factory import create_transport
from chimera.core.transport_redis import RedisTransport

import pytest


def test_create_transport():
    transport = create_transport("nng://localhost:8080")
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert isinstance(transport, TransportNNG)

    transport = create_transport("redis://localhost:8080")
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert isinstance(transport, RedisTransport)


def test_create_default_transport_win32(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")

    transport = create_transport("localhost:8080")
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert isinstance(transport, TransportNNG)


def test_create_redis_transport_on_win32(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")

    with pytest.raises(ValueError):
        create_transport("redis//localhost:8080")


def test_create_default_transport_linux(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")

    transport = create_transport("localhost:8080")
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert isinstance(transport, RedisTransport)


def test_create_default_transport_macos(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")

    transport = create_transport("localhost:8080")
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert isinstance(transport, RedisTransport)


def test_create_transport_errors():
    with pytest.raises(ValueError):
        create_transport("localhost:")

    with pytest.raises(ValueError):
        create_transport("invalid://localhost:8080")
