from typing import override

import pynng

from chimera.core.transport import Transport


class TransportNNG(Transport):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self._rpc_socket = None

    @override
    def bind(self):
        self._rpc_socket = pynng.Rep0()
        self._rpc_socket.listen(f"tcp://{self.host}:{self.port}")

    @override
    def connect(self):
        self._rpc_socket = pynng.Req0()
        self._rpc_socket.dial(f"tcp://{self.host}:{self.port}")

    @override
    def close(self):
        assert self._rpc_socket is not None
        self._rpc_socket.close()

    @override
    def ping(self) -> bool:
        return True

    @override
    def send(self, data: bytes) -> None:
        assert self._rpc_socket is not None
        self._rpc_socket.send(data)

    @override
    def recv(self) -> bytes | None:
        assert self._rpc_socket is not None
        return self._rpc_socket.recv()
