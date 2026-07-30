# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""Refcounted bridge between bus subscriptions and WS sessions.

The bus holds ONE subscription per (publisher, event) no matter how many WS
clients asked for it; the broker fans events out to every interested session.
Two bus facts force this shape: Bus.subscribe dedups by callable equality
(re-subscribing the same callable is a silent local no-op), and event
callbacks are invoked with only the payload — so each (publisher, event)
gets its own closure that carries its identity.

Callbacks run on bus handler-pool threads; they immediately hop to the
asyncio loop with call_soon_threadsafe. All entry/session bookkeeping runs
on the loop thread only.
"""

import logging
import time
from typing import TYPE_CHECKING

from chimera.controllers.ws import protocol as ws

if TYPE_CHECKING:
    from chimera.controllers.ws.gateway import GatewayCore
    from chimera.controllers.ws.session import Session

log = logging.getLogger(__name__)

# (canonical publisher URL, event name)
type SubscriptionKey = tuple[str, str]


class _Entry:
    def __init__(self, display_path: str, callback):
        self.display_path = display_path
        self.callback = callback
        self.sessions: set[Session] = set()


class SubscriptionBroker:
    def __init__(self, core: "GatewayCore"):
        self._core = core
        self._entries: dict[SubscriptionKey, _Entry] = {}

    def _make_callback(self, key: SubscriptionKey):
        def callback(*args, **kwargs):
            # bus handler-pool thread: never block here, just hop to the loop
            loop = self._core.loop
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(self._fanout, key, args, kwargs)

        return callback

    async def acquire(
        self, key: SubscriptionKey, display_path: str, session: "Session"
    ) -> None:
        entry = self._entries.get(key)
        if entry is not None:
            entry.sessions.add(session)
            return

        entry = _Entry(display_path, self._make_callback(key))
        entry.sessions.add(session)
        self._entries[key] = entry

        publisher, event = key
        try:
            await self._core.call_bus(
                self._core.bus.subscribe,
                sub=self._core.gateway_url,
                pub=publisher,
                event=event,
                callback=entry.callback,
            )
        except Exception:
            entry.sessions.discard(session)
            if not entry.sessions:
                self._entries.pop(key, None)
            raise

    async def release(self, key: SubscriptionKey, session: "Session") -> None:
        entry = self._entries.get(key)
        if entry is None:
            return
        entry.sessions.discard(session)
        if entry.sessions:
            return

        del self._entries[key]
        publisher, event = key
        try:
            await self._core.call_bus(
                self._core.bus.unsubscribe,
                sub=self._core.gateway_url,
                pub=publisher,
                event=event,
                callback=entry.callback,
            )
        except Exception:
            log.warning(
                f"unsubscribe from {event} on {publisher} failed", exc_info=True
            )

    def _fanout(self, key: SubscriptionKey, args: tuple, kwargs: dict) -> None:
        # loop thread: encode once, enqueue everywhere
        entry = self._entries.get(key)
        if entry is None:
            return  # events racing an unsubscribe: drop
        frame = ws.encode(
            ws.Event(
                path=entry.display_path,
                event=key[1],
                args=list(args),
                kwargs=kwargs,
                ts=int(time.time() * 1000),
            )
        )
        for session in entry.sessions:
            session.enqueue_event(frame)

    async def reassert(self) -> None:
        """Re-push every subscription on the wire after the server lost them
        (it drops subscriber state when it evicts a peer). unsubscribe+
        subscribe with the same closure forces Bus.subscribe past its local
        dedup; stale tokens left on the publisher are harmless (delivery is
        per subscriber bus, not per token)."""
        for key, entry in list(self._entries.items()):
            publisher, event = key
            try:
                await self._core.call_bus(
                    self._core.bus.unsubscribe,
                    sub=self._core.gateway_url,
                    pub=publisher,
                    event=event,
                    callback=entry.callback,
                )
                await self._core.call_bus(
                    self._core.bus.subscribe,
                    sub=self._core.gateway_url,
                    pub=publisher,
                    event=event,
                    callback=entry.callback,
                )
            except Exception:
                log.warning(
                    f"re-subscribe to {event} on {publisher} failed", exc_info=True
                )

    def stats(self) -> dict:
        return {
            key[0] + "/" + key[1]: len(entry.sessions)
            for key, entry in self._entries.items()
        }
