import sys
import urllib.parse

from typing import Type

from .transport import Transport
from .transport_nng import TransportNNG

from .serializer import Serializer
from .serializer_pickle import PickleSerializer


if sys.platform != "win32":
    from .transport_redis import RedisTransport


def default_transport() -> str:
    if sys.platform == "win32":
        return "nng"
    else:
        return "redis"


def default_serializer_for_transport(transport: str) -> Type[Serializer]:
    if transport == "nng":
        return PickleSerializer
    elif transport == "redis":
        return PickleSerializer
    else:
        raise ValueError("Unsupported transport protocol")


def create_transport(url: str) -> Transport:
    use_default_transport = "://" not in url

    if use_default_transport:
        url = f"{default_transport()}://{url}"

    url_parts = urllib.parse.urlparse(url)

    transport = url_parts.scheme
    host = url_parts.hostname
    port = url_parts.port

    if host is None or port is None:
        raise ValueError("Invalid URL")

    serializer = default_serializer_for_transport(transport)

    if transport == "nng":
        return TransportNNG(host, port, serializer=serializer)
    elif transport == "redis":
        if sys.platform == "win32":
            raise ValueError("Redis transport is not supported on Windows")

        return RedisTransport(host, int(port), serializer=serializer)
    else:
        raise ValueError("Unsupported transport protocol")
