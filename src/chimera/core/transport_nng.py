import logging
from typing import override, Type, cast
from dataclasses import dataclass, field

import pynng

from chimera.core.protocol import Request, Response, Event
from chimera.core.serializer import Serializer
from chimera.core.transport import Transport

log = logging.getLogger(__name__)


@dataclass
class NNGRequest(Request):
    ctx: pynng.Context | None = field(init=False)


class TransportNNG(Transport):
    def __init__(self, host: str, port: int, serializer: Type[Serializer]):
        super().__init__(host, port, serializer)

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
    def send_request(self, request: Request) -> None:
        assert self._rpc_socket is not None
        self._rpc_socket.send(request.dump(self.serializer))

    @override
    def recv_request(self) -> Request | None:
        assert self._rpc_socket is not None

        ctx = self._rpc_socket.new_context()
        data = ctx.recv()

        nng_request = NNGRequest.load(self.serializer, data)
        # TODO: fix error handling
        assert nng_request is not None
        nng_request.ctx = ctx

        return nng_request

    @override
    def send_response(self, request: Request, response: Response) -> None:
        assert self._rpc_socket is not None

        nng_request: NNGRequest = cast(NNGRequest, request)
        assert hasattr(nng_request, "ctx")

        nng_request.ctx.send(response.dump(self.serializer))

    @override
    def recv_response(self, request: Request) -> Response | None:
        assert self._rpc_socket is not None
        data = self._rpc_socket.recv()
        return Response.load(self.serializer, data)

    @override
    def publish(self, topic: str, event: Event) -> None: ...

    @override
    def subscribe(self, topic: str, callback) -> None: ...

    @override
    def unsubscribe(self, topic: str, callback) -> None: ...
