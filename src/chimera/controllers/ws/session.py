# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""One WS connection: handshake, request dispatch, event delivery, cleanup.

All outbound frames go through a single bounded queue drained by one writer
task, so results and events never interleave mid-frame and a slow consumer
never blocks the loop: results/errors await queue space (per-session
backpressure), events are fire-and-forget and get dropped (with a counter)
when the queue is full.

Every call runs as its own asyncio task: a minutes-long slew must not stop
the reader from serving other requests on the same connection.
"""

import asyncio
import logging

import msgspec
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from chimera.controllers.ws import introspect
from chimera.controllers.ws import protocol as ws
from chimera.controllers.ws.gateway import GatewayCore, WsError
from chimera.core.url import parse_url

log = logging.getLogger(__name__)

HELLO_TIMEOUT = 10.0  # s
OUTBOX_SIZE = 1000


class Session:
    def __init__(self, core: GatewayCore, connection: ServerConnection):
        self.core = core
        self.connection = connection
        self.subs: set[tuple[str, str]] = set()
        self.outbox: asyncio.Queue[bytes] = asyncio.Queue(maxsize=OUTBOX_SIZE)
        self.dropped_events = 0
        self._tasks: set[asyncio.Task] = set()

    async def run(self) -> None:
        writer = asyncio.create_task(self._writer())
        try:
            if not await self._handshake():
                return
            async for frame in self.connection:
                await self._dispatch(frame)
        except ConnectionClosed:
            pass
        finally:
            writer.cancel()
            for task in self._tasks:
                task.cancel()
            for key in list(self.subs):
                self.subs.discard(key)
                try:
                    await self.core.broker.release(key, self)
                except Exception:
                    log.warning("subscription cleanup failed", exc_info=True)
            if self.dropped_events:
                log.warning(
                    f"session closed with {self.dropped_events} events dropped "
                    "(slow consumer)"
                )

    #
    # outbound
    #

    async def send(self, message: ws.WsMessage) -> None:
        await self.outbox.put(ws.encode(message))

    def enqueue_event(self, frame: bytes) -> None:
        try:
            self.outbox.put_nowait(frame)
        except asyncio.QueueFull:
            self.dropped_events += 1
            if self.dropped_events == 1 or self.dropped_events % 100 == 0:
                log.warning(f"slow WS consumer: {self.dropped_events} events dropped")

    async def _writer(self) -> None:
        try:
            while True:
                frame = await self.outbox.get()
                # decode: JSON must go out as TEXT frames — bytes become
                # BINARY frames, which browsers surface as Blobs
                await self.connection.send(frame.decode())
        except ConnectionClosed:
            pass

    async def _error(
        self, id: str | None, code: str, message: str, details=None
    ) -> None:
        await self.send(ws.Error(id=id, code=code, message=message, details=details))

    #
    # handshake
    #

    async def _handshake(self) -> bool:
        try:
            frame = await asyncio.wait_for(self.connection.recv(), HELLO_TIMEOUT)
        except (TimeoutError, ConnectionClosed):
            return False

        try:
            message = ws.decode_client_message(frame)
        except msgspec.DecodeError:
            message = None

        if not isinstance(message, ws.Hello):
            await self._reject(
                ws.ERROR_PROTOCOL_ERROR,
                "first message must be hello",
                ws.CLOSE_PROTOCOL_ERROR,
            )
            return False

        if message.protocol != ws.PROTOCOL_VERSION:
            await self._reject(
                ws.ERROR_UNSUPPORTED_PROTOCOL,
                f"unsupported protocol {message.protocol}, "
                f"server speaks {ws.PROTOCOL_VERSION}",
                ws.CLOSE_UNSUPPORTED_PROTOCOL,
            )
            return False

        # v1 accepts any auth (trusted network); the field exists so a
        # token-checking v2 server can reject old clients cleanly
        await self.send(self.core.welcome())
        return True

    async def _reject(self, code: str, message: str, close_code: int) -> None:
        # handshake failures bypass the outbox: nothing else is in flight and
        # the frame must be on the wire before close
        try:
            await self.connection.send(
                ws.encode(ws.Error(id=None, code=code, message=message)).decode()
            )
            await self.connection.close(close_code, message[:120])
        except ConnectionClosed:
            pass

    #
    # dispatch
    #

    async def _dispatch(self, frame: str | bytes) -> None:
        try:
            message = ws.decode_client_message(frame)
        except msgspec.DecodeError as error:
            await self._error(
                None, ws.ERROR_BAD_REQUEST, f"undecodable message: {error}"
            )
            return

        match message:
            case ws.Call():
                self._spawn(self._handle_call(message))
            case ws.Subscribe():
                self._spawn(self._handle_subscribe(message))
            case ws.Unsubscribe():
                self._spawn(self._handle_unsubscribe(message))
            case ws.ListObjects():
                self._spawn(self._handle_list(message))
            case ws.Describe():
                self._spawn(self._handle_describe(message))
            case ws.GetSchema():
                await self.send(
                    ws.Result(id=message.id, value=introspect.load_schema())
                )
            case ws.Ping():
                await self.send(ws.Pong(id=message.id))
            case ws.Hello():
                await self._error(
                    None, ws.ERROR_PROTOCOL_ERROR, "hello already received"
                )

    def _spawn(self, coroutine) -> None:
        task = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    #
    # handlers (each one its own task; every path answers exactly once)
    #

    async def _handle_call(self, message: ws.Call) -> None:
        try:
            value = await self.core.request(
                message.path,
                message.method,
                args=message.args,
                kwargs=message.kwargs,
                timeout=message.timeout,
            )
        except WsError as error:
            await self._error(message.id, error.code, error.message, error.details)
            return
        except Exception as error:
            log.exception(f"call {message.method} on {message.path} blew up")
            await self._error(message.id, ws.ERROR_REMOTE_ERROR, str(error))
            return

        try:
            await self.send(ws.Result(id=message.id, value=value))
        except msgspec.EncodeError as error:
            await self._error(
                message.id,
                ws.ERROR_REMOTE_ERROR,
                f"result of {message.method} is not JSON-encodable: {error}",
            )

    async def _handle_subscribe(self, message: ws.Subscribe) -> None:
        try:
            resolved = await self.core.resolve(message.path)
        except WsError as error:
            await self._error(message.id, error.code, error.message, error.details)
            return

        display_path = parse_url(resolved).path
        key = (resolved, message.event)
        try:
            await self.core.broker.acquire(key, display_path, self)
        except Exception as error:
            log.exception(f"subscribe to {message.event} on {resolved} failed")
            await self._error(message.id, ws.ERROR_UNAVAILABLE, str(error))
            return

        self.subs.add(key)
        await self.send(
            ws.Result(
                id=message.id, value={"path": display_path, "event": message.event}
            )
        )

    async def _handle_unsubscribe(self, message: ws.Unsubscribe) -> None:
        try:
            resolved = await self.core.resolve(message.path)
        except WsError as error:
            await self._error(message.id, error.code, error.message, error.details)
            return

        key = (resolved, message.event)
        if key in self.subs:
            self.subs.discard(key)
            await self.core.broker.release(key, self)
        # idempotent: unsubscribing something not subscribed is not an error
        await self.send(
            ws.Result(
                id=message.id,
                value={"path": parse_url(resolved).path, "event": message.event},
            )
        )

    async def _handle_list(self, message: ws.ListObjects) -> None:
        try:
            status = await self.core.manager_status()
        except WsError as error:
            await self._error(message.id, error.code, error.message, error.details)
            return
        await self.send(ws.Result(id=message.id, value=introspect.list_objects(status)))

    async def _handle_describe(self, message: ws.Describe) -> None:
        try:
            resolved = await self.core.resolve(message.path)
            status = await self.core.manager_status()
        except WsError as error:
            await self._error(message.id, error.code, error.message, error.details)
            return

        path = parse_url(resolved).path
        entry = next(
            (o for o in status["objects"] if o["path"] == path),
            None,
        )
        if entry is None:
            self.core.invalidate(message.path)
            await self._error(
                message.id, ws.ERROR_NOT_FOUND, f"no object at {message.path}"
            )
            return
        await self.send(
            ws.Result(id=message.id, value=introspect.describe_object(entry))
        )
