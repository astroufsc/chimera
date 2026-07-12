from typing import override

import pynng

from chimera.core.transport import Transport


class TransportNNG(Transport):
    def __init__(self, url: str):
        super().__init__(url)

        self._sk = None

    def ping(self) -> bool:
        # FIXME: add protocol support for it?
        return True

    @override
    def bind(self):
        self._sk = pynng.Pull0()
        self._sk.listen(f"{self.url}")

    @override
    def connect(self):
        self._sk = pynng.Push0()
        # block sends up to this long when the send buffer is full
        # (backpressure), instead of silently dropping messages under load.
        # A dead peer still fails the send with a Timeout after this period.
        self._sk.send_timeout = 5000  # ms
        self._sk.dial(f"{self.url}", block=True)

    @override
    def close(self):
        assert self._sk is not None
        self._sk.close()
        del self._sk
        self._sk = None

    @override
    def send(self, data: bytes) -> bool:
        assert self._sk is not None
        try:
            # blocking send (up to send_timeout): waits for buffer space
            # instead of dropping messages when sending faster than the
            # receiver can keep up
            self._sk.send(data, block=True)
            return True
        except pynng.TryAgain:
            # Would block - send buffer is full
            return False
        except (pynng.Closed, pynng.ConnectionRefused, pynng.exceptions.Timeout):
            # Connection is dead or refusing
            return False
        except Exception:
            # Any other error - log it but don't crash
            return False

    @override
    def recv(self) -> bytes:
        assert self._sk is not None
        return self._sk.recv(block=False)

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
