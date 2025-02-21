import logging
import threading
from typing import override

import pynng

from chimera.core.transport import Transport

log = logging.getLogger(__name__)


class TransportNNG(Transport):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self._rpc_socket = None
        self._thread_id = None

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
        # if self._thread_id is None or self._thread_id != threading.current_thread().native_id:
        # log.warning("send() called from different thread")
        # # print stack trace
        # import traceback
        # traceback.print_stack()

    @override
    def recv(self, block=True) -> bytes | None:
        assert self._rpc_socket is not None
        # if self._thread_id is None or self._thread_id != threading.current_thread().native_id:
        # log.warning("send() called from different thread")
        # # print stack trace
        # import traceback
        # traceback.print_stack()
        return self._rpc_socket.recv(block=block)
