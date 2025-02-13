from typing import Type


class Transport:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def bind(self): ...

    def connect(self): ...

    def close(self): ...

    def ping(self) -> bool: ...

    # TODO: return int?
    def send(self, data: bytes) -> None: ...

    def recv(self) -> bytes | None: ...

    def publish(self, topic: str, data: bytes) -> int: ...

    def subscribe(self, topic: str, callback) -> None: ...

    def unsubscribe(self, topic: str, callback) -> None: ...


def create_transport(host: str, port: int, transport_cls: Type[Transport]) -> Transport:
    return transport_cls(host, port)
