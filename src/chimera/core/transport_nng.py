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
        # nng's default send buffer is ZERO: a non-blocking send succeeds only
        # if the pipe can take the message at that exact instant, so any
        # back-to-back burst (a CLI subscribing to several events, an event
        # storm) drops messages against a perfectly healthy peer. Buffer the
        # bursts; sustained backpressure still surfaces as AGAIN.
        self._sk.send_buffer_size = 128
        # registered before dial so no removal event can be missed
        self._sk.add_post_pipe_remove_cb(self._pipe_removed)
        try:
            self._sk.dial(f"{self.url}", block=True)
        except Exception as e:
            log.debug(f"connect failed: {e}")
            self._sk.close()
            self._sk = None
            raise

    def _pipe_removed(self, pipe: pynng.Pipe) -> None:
        # runs on an nng worker thread: socket operations are not allowed here
        # (nng#1665) — only notify whoever is watching
        callback = self.on_disconnect
        if callback is not None:
            callback()

    @override
    def close(self):
        if self._sk is None:
            return
        # closing removes our own pipes: that is not a peer loss
        self.on_disconnect = None
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
