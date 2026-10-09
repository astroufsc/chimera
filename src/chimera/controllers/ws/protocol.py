# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""WebSocket envelope protocol between browsers and the WS gateway.

This is deliberately *not* the internal bus protocol (chimera.core.protocol):
bus messages carry peer bus URLs, monotonic-ns timestamps and integer ids
larger than 2^53, none of which belong in a browser. The envelope keeps the
same style (msgspec tagged union discriminated by a "type" field, snake_case
fields) so it feels native on both sides of the bridge.

The TypeScript mirror of these types lives in ts/src/protocol.ts.
"""

from typing import Any

import msgspec

PROTOCOL_VERSION = 1

# WebSocket close codes (4000-4999 = application-defined)
CLOSE_UNSUPPORTED_PROTOCOL = 4001
CLOSE_PROTOCOL_ERROR = 4002
CLOSE_AUTH_FAILED = 4003

# error codes carried by Error.code
ERROR_NOT_FOUND = "not_found"  # bus 404
ERROR_BUSY = "busy"  # bus 503 (lane full)
ERROR_REMOTE_ERROR = "remote_error"  # bus 500 (message carries traceback text)
ERROR_TIMEOUT = "timeout"  # call timeout elapsed (op may still complete!)
ERROR_UNAVAILABLE = "unavailable"  # bus dead / peer unreachable
ERROR_BAD_REQUEST = "bad_request"  # malformed message / bad path
ERROR_PROTOCOL_ERROR = "protocol_error"  # hello violations and friends
ERROR_AUTH_REQUIRED = "auth_required"
ERROR_AUTH_FAILED = "auth_failed"
ERROR_UNSUPPORTED_PROTOCOL = "unsupported_protocol"


class WsMessage(msgspec.Struct, tag=str.lower, frozen=True):
    pass


class AuthInfo(msgspec.Struct, frozen=True):
    scheme: str
    token: str


#
# client -> server
#


class Hello(WsMessage, frozen=True):
    """Must be the first message on a connection.

    auth is reserved for future token authentication: servers that require it
    reply with an auth_required/auth_failed error and close with
    CLOSE_AUTH_FAILED.
    """

    protocol: int
    auth: AuthInfo | None = None


class Call(WsMessage, frozen=True):
    """Invoke a method on a bus object.

    id is a client-generated correlation string echoed on result/error.
    timeout (seconds) bounds only the *wait*: on timeout the remote operation
    may still run to completion — there is no cancellation on the bus.
    """

    id: str
    path: str
    method: str
    args: list = []
    kwargs: dict = {}
    timeout: float | None = None


class Subscribe(WsMessage, frozen=True):
    id: str
    path: str
    event: str


class Unsubscribe(WsMessage, frozen=True):
    id: str
    path: str
    event: str


class ListObjects(WsMessage, frozen=True, tag="list"):
    id: str


class Describe(WsMessage, frozen=True):
    id: str
    path: str


class GetSchema(WsMessage, frozen=True, tag="schema"):
    id: str


class Ping(WsMessage, frozen=True):
    id: str


#
# server -> client
#


class Welcome(WsMessage, frozen=True):
    protocol: int
    server: dict[str, str]
    auth: str = "none"


class Result(WsMessage, frozen=True):
    id: str
    value: Any = None


class Error(WsMessage, frozen=True):
    """id echoes the failed request; None for connection-level errors."""

    id: str | None
    code: str
    message: str
    details: Any = None


class Event(WsMessage, frozen=True):
    """A bus event delivered to a subscriber.

    path is the resolved canonical object path (as echoed by the subscribe
    result), args/kwargs the published payload, ts server wall-clock in ms.
    """

    path: str
    event: str
    args: list
    kwargs: dict
    ts: int


class Pong(WsMessage, frozen=True):
    id: str


type ClientMessage = (
    Hello | Call | Subscribe | Unsubscribe | ListObjects | Describe | GetSchema | Ping
)
type ServerMessage = Welcome | Result | Error | Event | Pong

_encoder = msgspec.json.Encoder()
_client_decoder = msgspec.json.Decoder(ClientMessage)
_server_decoder = msgspec.json.Decoder(ServerMessage)


def encode(message: WsMessage) -> bytes:
    return _encoder.encode(message)


def decode_client_message(data: bytes | str) -> ClientMessage:
    """Decode a browser frame; raises msgspec.DecodeError on garbage."""
    return _client_decoder.decode(data)


def decode_server_message(data: bytes | str) -> ServerMessage:
    """Decode a gateway frame (used by tests and Python WS clients)."""
    return _server_decoder.decode(data)
