import functools
from typing import Type

from chimera.core.protocol import Event, Request, Response
from chimera.core.serializer import Serializer


class Transport:
    def __init__(self, host: str, port: int, serializer: Type[Serializer]):
        self.serializer = serializer()
        self.host = host
        self.port = port

    def bind(self): ...

    def connect(self): ...

    def close(self): ...

    def ping(self) -> bool: ...

    def send_request(self, request: Request) -> None: ...

    def recv_request(self) -> Request: ...

    def send_response(self, request: Request, response: Response) -> None: ...

    def recv_response(self, request: Request) -> Response: ...

    def publish(self, topic: str, data: Event) -> int: ...

    def subscribe(self, topic: str, callback) -> None: ...

    def unsubscribe(self, channel: str, callback) -> None: ...


@functools.cache
def create_transport(
    host: str, port: int, transport_cls: Type[Transport], serializer: Type[Serializer]
) -> Transport:
    """
    Create a transport instance. Using functools.cache to avoid creating multiple instances.
    """
    return transport_cls(host, port, serializer)
