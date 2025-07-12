import random
import time
import traceback
from functools import cached_property
from typing import Any, override

import msgspec

from chimera.core.url import parse_url

type Timestamp = int

type Messages = (
    Request | Response | Subscribe | Publish | Unsubscribe | Event | Ping | Pong
)


class Message(msgspec.Struct, tag=str.lower, frozen=True, dict=True):
    ts: Timestamp

    @cached_property
    def src_bus(self) -> str:
        raise NotImplementedError()

    @cached_property
    def dst_bus(self) -> str:
        raise NotImplementedError()


class RpcMessage(Message, frozen=True):
    src: str  # an URL [tcp://]host:port/Object/instance
    dst: str  # an URL [tcp://]host:port/Object/[0|instance]

    @cached_property
    @override
    def src_bus(self) -> str:
        return parse_url(self.src).url

    @cached_property
    @override
    def dst_bus(self) -> str:
        return parse_url(self.dst).url


class Ping(RpcMessage, frozen=True):
    id: int
    ok: bool = False

    def pong(self) -> "Pong":
        return Pong(
            ts=Protocol.timestamp(),
            src=self.dst,
            dst=self.src,
            id=self.id,
            ok=True,
        )


class Pong(RpcMessage, frozen=True):
    id: int
    ok: bool = True


class Request(RpcMessage, frozen=True):
    id: int  # number to identify this request

    method: str  # get_az

    args: list[Any]
    kwargs: dict[str, Any]

    def ok(self, result: Any) -> "Response":
        return Response(
            ts=Protocol.timestamp(),
            src=self.dst,
            dst=self.src,
            id=self.id,
            code=200,
            result=result,
        )

    def not_found(self, msg: str) -> "Response":
        return Response(
            ts=Protocol.timestamp(),
            src=self.dst,
            dst=self.src,
            id=self.id,
            code=404,
            error=msg,
        )

    def error(self, error: Exception) -> "Response":
        tb = "".join(traceback.format_exception(error))
        return Response(
            ts=Protocol.timestamp(),
            src=self.dst,
            dst=self.src,
            id=self.id,
            code=500,
            error=f"{error.__class__.__name__}: {str(error)} (traceback={tb})",
        )


class Response(RpcMessage, frozen=True):
    id: int  # to correlate with the original request

    code: int

    result: Any | None = None
    # TODO: how to expose exception backtraces?
    error: str | None = None


class SubMessage(Message, frozen=True):
    pub: str  # an URL [tcp://]host:port/Object/[0|instance]
    sub: str  # an URL [tcp://]host:port/Object/[0|instance]

    @cached_property
    @override
    def src_bus(self) -> str:
        return parse_url(self.pub).url

    @cached_property
    @override
    def dst_bus(self) -> str:
        return parse_url(self.sub).url


class Subscribe(SubMessage, frozen=True):
    # late-binding: someone can subscribe to events that are not yet bound to any publishers
    event: str  # slew_complete

    # an id representing the callbackas we cannot pass a reference to the callable
    callback: int  #  id(self.on_slew_complete)


class Unsubscribe(SubMessage, frozen=True):
    event: str  # slew_complete

    # an id representing the callbackas we cannot pass a reference to the callable
    callback: int  #  id(self.on_slew_complete)


class PubMessage(Message, frozen=True):
    pub: str  # an URL [tcp://]host:port/Object/[0|instance]

    @cached_property
    @override
    def src_bus(self) -> str:
        return parse_url(self.pub).url

    @cached_property
    @override
    def dst_bus(self) -> str:
        return parse_url(self.pub).url


class Publish(PubMessage, frozen=True):
    event: str  # slew_complete

    args: list[Any]
    kwargs: dict[str, Any]

    def callback(
        self, *, dst: str, event: str, args: list[Any], kwargs: dict[str, Any]
    ) -> "Event":
        return Event(
            ts=Protocol.timestamp(),
            src=self.pub,
            dst=dst,
            event=event,
            args=args,
            kwargs=kwargs,
        )


class Event(RpcMessage, frozen=True):
    event: str  # slew_complete

    args: list[Any]
    kwargs: dict[str, Any]

    @cached_property
    @override
    def dst_bus(self) -> str:
        # for events, dst is just the bus address, so we cannot parse it as a full url with path
        return self.dst


class Protocol:
    @staticmethod
    def id() -> int:
        return random.randint(0, 2**32)

    @staticmethod
    def timestamp() -> int:
        # TODO: TAI?
        return time.monotonic_ns()

    @staticmethod
    def ping(*, src: str, dst: str) -> Ping:
        return Ping(
            ts=Protocol.timestamp(),
            src=src,
            dst=dst,
            id=Protocol.id(),
        )

    @staticmethod
    def request(
        *,
        src: str,
        dst: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Request:
        return Request(
            id=Protocol.id(),
            ts=Protocol.timestamp(),
            src=src,
            dst=dst,
            method=method,
            args=args or [],
            kwargs=kwargs or {},
        )

    @staticmethod
    def subscribe(*, sub: str, pub: str, event: str, callback: int) -> Subscribe:
        return Subscribe(
            ts=Protocol.timestamp(),
            sub=sub,
            pub=pub,
            event=event,
            callback=callback,
        )

    @staticmethod
    def unsubscribe(*, sub: str, pub: str, event: str, callback: int) -> Unsubscribe:
        return Unsubscribe(
            ts=Protocol.timestamp(),
            sub=sub,
            pub=pub,
            event=event,
            callback=callback,
        )

    @staticmethod
    def publish(
        *,
        pub: str,
        event: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Publish:
        return Publish(
            ts=Protocol.timestamp(),
            pub=pub,
            event=event,
            args=args,
            kwargs=kwargs,
        )

    @staticmethod
    def error(*, src: str, dst: str, error: Exception) -> Response:
        tb = "".join(traceback.format_exception(error))
        return Response(
            ts=Protocol.timestamp(),
            src=src,
            dst=dst,
            id=Protocol.id(),
            code=500,
            error=f"{error.__class__.__name__}: {str(error)} (traceback={tb})",
        )
