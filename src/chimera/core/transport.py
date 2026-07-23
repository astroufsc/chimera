import enum


class SendResult(enum.StrEnum):
    OK = "ok"
    # send buffer full: peer is alive but not keeping up (backpressure)
    AGAIN = "again"
    # socket closed, connection refused or errored
    DEAD = "dead"


class Transport:
    def __init__(self, url: str):
        self.url = url

    def bind(self) -> None: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def send(self, data: bytes) -> SendResult: ...

    def recv(self) -> bytes | None: ...

    def recv_fd(self) -> int: ...

    def send_fd(self) -> int: ...
