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
        sk = pynng.Pull0()
        try:
            sk.listen(f"{self.url}")
        except Exception:
            try:
                sk.close()
            except Exception:
                pass
            raise
        self._sk = sk

    @override
    def connect(self):
        sk = pynng.Push0()
        try:
            sk.dial(f"{self.url}", block=True)
        except Exception:
            try:
                sk.close()
            except Exception:
                pass
            raise
        self._sk = sk

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
            self._sk.send(data, block=False)
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
