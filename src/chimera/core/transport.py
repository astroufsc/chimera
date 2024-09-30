from typing import Type

from chimera.core.protocol import Request, Response
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
