# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""The WebSocket gateway core: an asyncio websockets server bridged to the
thread-based Bus.

One thread runs the asyncio loop with the WS server. Bus operations (request,
ping, subscribe) block, so sessions run them on a dedicated executor via
run_in_executor; bus events hop the other way with call_soon_threadsafe (see
broker.py). The Bus itself is thread-safe: replies are correlated by request
id, so any number of executor threads can wait concurrently.

The same core backs both deployment shapes: embedded in the server process by
the WsGateway controller (bus = the manager's own bus, all delivery local) or
in a standalone chimera-ws process (bus = its own peer bus; standalone=True
adds the watchdog that re-asserts subscriptions after the server evicts us,
because the bus has no automatic re-subscribe).
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from websockets.asyncio.server import serve

from chimera.controllers.ws import protocol as ws
from chimera.controllers.ws.broker import SubscriptionBroker
from chimera.core.bus import Bus
from chimera.core.exceptions import BusDeadException, RequestTimeoutException
from chimera.core.protocol import Response
from chimera.core.url import parse_url, resolve_url
from chimera.core.version import chimera_version

log = logging.getLogger(__name__)

RESUBSCRIBE_WATCHDOG_INTERVAL = 30.0  # s, matches the bus health-check period


class WsError(Exception):
    """A request-level failure that maps to an error frame."""

    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class GatewayCore:
    def __init__(
        self,
        *,
        bus: Bus,
        gateway_url: str,
        manager_url: str,
        ws_host: str = "0.0.0.0",
        ws_port: int = 7667,
        max_calls: int = 64,
        standalone: bool = False,
    ):
        self.bus = bus
        # src of our requests and sub of our subscriptions: the controller's
        # own location in controller mode, a synthetic /WsGateway/... URL on
        # the gateway's bus in standalone mode
        self.gateway_url = str(gateway_url)
        self.manager_url = str(manager_url)
        # relative paths (/Telescope/0) resolve against the *server's* bus,
        # which in standalone mode is not our own
        self.server_bus = parse_url(self.manager_url).bus
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.standalone = standalone

        self.broker = SubscriptionBroker(self)
        self.loop: asyncio.AbstractEventLoop | None = None

        self._executor = ThreadPoolExecutor(
            max_workers=max_calls, thread_name_prefix="chimera-ws-call"
        )
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._startup_error: BaseException | None = None
        self._stop_requested: asyncio.Event | None = None

        self._resolve_cache: dict[str, str] = {}
        self._resolve_lock = threading.Lock()

    #
    # lifecycle (called from bus/manager threads)
    #

    def start(self, timeout: float = 10.0) -> None:
        self._thread = threading.Thread(
            target=self._run, name="chimera-ws-loop", daemon=True
        )
        self._thread.start()
        if not self._started.wait(timeout):
            raise RuntimeError("WS gateway did not start in time")
        if self._startup_error is not None:
            raise RuntimeError("WS gateway failed to start") from self._startup_error

    def stop(self) -> None:
        if self.loop is not None and self._stop_requested is not None:
            try:
                self.loop.call_soon_threadsafe(self._stop_requested.set)
            except RuntimeError:
                pass  # loop already closed
        if self._thread is not None:
            self._thread.join(timeout=10.0)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run(self) -> None:
        try:
            asyncio.run(self._main())
        except BaseException as error:  # startup failures (port in use, ...)
            self._startup_error = error
            self._started.set()
            log.exception("WS gateway loop died")

    async def _main(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._stop_requested = asyncio.Event()

        # import here to avoid a circular import (session imports gateway)
        from chimera.controllers.ws.session import Session

        async def handler(connection) -> None:
            await Session(self, connection).run()

        watchdog = None
        async with serve(handler, self.ws_host, self.ws_port):
            log.info(f"WS gateway listening on ws://{self.ws_host}:{self.ws_port}")
            if self.standalone:
                watchdog = asyncio.create_task(self._resubscribe_watchdog())
            self._started.set()
            try:
                await self._stop_requested.wait()
            finally:
                if watchdog is not None:
                    watchdog.cancel()

    #
    # bus bridging (called from the asyncio loop)
    #

    async def call_bus(self, fn, /, **kwargs) -> Any:
        assert self.loop is not None
        return await self.loop.run_in_executor(self._executor, partial(fn, **kwargs))

    async def resolve(self, path: str) -> str:
        """Resolve a browser path like /Telescope/0 to the canonical full URL
        of the object on the server bus, via ping (like Proxy.resolve)."""
        with self._resolve_lock:
            cached = self._resolve_cache.get(path)
        if cached is not None:
            return cached

        try:
            # bare /Class/name paths resolve against the server's bus;
            # full host:port/Class/name URLs pass through unchanged
            destination = resolve_url(path, self.server_bus).url
        except ValueError as error:
            raise WsError(ws.ERROR_BAD_REQUEST, f"invalid path {path!r}") from error

        pong = await self.call_bus(
            self.bus.ping, src=self.gateway_url, dst=destination, timeout=5.0
        )
        if pong is None or not pong.ok:
            raise WsError(ws.ERROR_NOT_FOUND, f"no object at {path}")
        resolved = pong.resolved_url or destination

        with self._resolve_lock:
            self._resolve_cache[path] = resolved
        return resolved

    def invalidate(self, path: str) -> None:
        with self._resolve_lock:
            self._resolve_cache.pop(path, None)

    async def request(
        self,
        path: str,
        method: str,
        args: list | None = None,
        kwargs: dict | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Resolve, call over the bus, and map failures to WsError."""
        resolved = await self.resolve(path)
        try:
            response: Response = await self.call_bus(
                self.bus.request,
                src=self.gateway_url,
                dst=resolved,
                method=method,
                args=args or [],
                kwargs=kwargs or {},
                timeout=timeout,
            )
        except RequestTimeoutException as error:
            raise WsError(ws.ERROR_TIMEOUT, str(error)) from error
        except BusDeadException as error:
            raise WsError(ws.ERROR_UNAVAILABLE, str(error)) from error

        if response.code == 200:
            return response.result
        if response.code == 404:
            # the object may have been removed: force a fresh resolution next
            # time instead of pinning a stale canonical URL
            self.invalidate(path)
            raise WsError(ws.ERROR_NOT_FOUND, response.error or f"{path} not found")
        if response.code == 503:
            raise WsError(ws.ERROR_BUSY, response.error or f"{path} is busy")
        raise WsError(
            ws.ERROR_REMOTE_ERROR, response.error or f"{method} failed on {path}"
        )

    async def manager_status(self) -> dict:
        return await self.request(self.manager_url, "get_status")

    def welcome(self) -> ws.Welcome:
        return ws.Welcome(
            protocol=ws.PROTOCOL_VERSION,
            server={"chimera": chimera_version},
            auth="none",
        )

    #
    # standalone-only: survive server-side eviction
    #

    async def _resubscribe_watchdog(self) -> None:
        """The server drops our subscriptions if it evicts us (>90 s of missed
        health pings, e.g. after a restart or partition). Detect the
        unreachable->reachable transition and re-assert every subscription."""
        reachable = True
        while True:
            await asyncio.sleep(RESUBSCRIBE_WATCHDOG_INTERVAL)
            try:
                pong = await self.call_bus(
                    self.bus.ping,
                    src=self.gateway_url,
                    dst=self.manager_url,
                    timeout=2.0,
                )
            except Exception:
                pong = None
            now_reachable = pong is not None and pong.ok
            if now_reachable and not reachable:
                log.info("server reachable again: re-asserting subscriptions")
                await self.broker.reassert()
            reachable = now_reachable
