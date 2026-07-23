import logging
from typing import override

import pynng

from chimera.core.transport import SendResult, Transport

log = logging.getLogger(__name__)


class TransportNNG(Transport):
    def __init__(self, url: str):
        super().__init__(url)

        self._sk = None

    @override
    def bind(self):
        self._sk = pynng.Pull0()
        try:
            self._sk.listen(f"{self.url}")
        except Exception as e:
            log.debug(f"bind failed: {e}")
            self._sk.close()
            self._sk = None
            raise

    @override
    def connect(self):
        self._sk = pynng.Push0()
        try:
            self._sk.dial(f"{self.url}", block=True)
        except Exception as e:
            log.debug(f"connect failed: {e}")
            self._sk.close()
            self._sk = None
            raise

    @override
    def close(self):
        if self._sk is None:
            return
        try:
            self._sk.close()
        except Exception as e:
            log.debug(f"close failed: {e}")

        self._sk = None

    @override
    def send(self, data: bytes) -> SendResult:
        if self._sk is None:
            return SendResult.DEAD
        try:
            self._sk.send(data, block=False)
            return SendResult.OK
        except pynng.TryAgain:
            # would block: send buffer is full but the peer is alive
            return SendResult.AGAIN
        except (pynng.Closed, pynng.ConnectionRefused, pynng.Timeout):
            return SendResult.DEAD
        except Exception:
            log.debug("transport: unexpected error sending", exc_info=True)
            return SendResult.DEAD

    @override
    def recv(self) -> bytes | None:
        if self._sk is None:
            return None
        try:
            return self._sk.recv(block=False)
        except (pynng.TryAgain, pynng.Closed):
            # TryAgain: fd polled readable but no message is available (spurious
            # wakeup or the queue was already drained); Closed: socket is gone.
            return None

    @override
    def recv_fd(self) -> int:
        if self._sk is None:
            return -1

        try:
            return self._sk.recv_fd
        except pynng.exceptions.Closed:
            return -1

    @override
    def send_fd(self) -> int:
        if self._sk is None:
            return -1

        try:
            return self._sk.send_fd
        except pynng.exceptions.Closed:
            return -1
