import logging
import os
import queue
import selectors
import threading
import time
from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, NamedTuple

import msgspec

from chimera.core.constants import LOCK_ATTRIBUTE_NAME, MANAGER_LOCATION
from chimera.core.exceptions import BusDeadException, RequestTimeoutException
from chimera.core.protocol import (
    Event,
    Messages,
    Ping,
    Pong,
    Protocol,
    Publish,
    Request,
    Response,
    Subscribe,
    Unsubscribe,
)
from chimera.core.transport import SendResult, Transport
from chimera.core.transport_factory import create_transport
from chimera.core.url import URL, create_url, parse_url

log = logging.getLogger(__name__)

# consecutive missed health pongs before a peer is declared gone
_MAX_MISSED_PONGS = 3


def pool_stats(pool: ThreadPoolExecutor) -> dict[str, Any]:
    """JSON-safe snapshot of a ThreadPoolExecutor: limits, backlog and
    per-thread state."""
    threads = [
        {
            "id": thread.native_id,
            "name": thread.name,
            "alive": thread.is_alive(),
            "daemon": thread.daemon,
        }
        for thread in list(pool._threads)
    ]

    return {
        "max_workers": pool._max_workers,
        "queued": pool._work_queue.qsize(),
        "threads": threads,
    }


type PublisherId = str
type SubscriberId = URL


class CallbackId:
    @classmethod
    def new(cls) -> int:
        # an opaque random token. id(callable) cannot work: every access to a
        # bound method creates a new object with a different id, so a later
        # unsubscribe(self.on_x) never matched and freed ids can even collide.
        # The client keeps a (sub, pub, event, callable) -> token map instead.
        return Protocol.id()


class EventId(NamedTuple):
    publisher: PublisherId
    event: str


@dataclass(frozen=True)
class Subscriber:
    subscriber: SubscriberId
    callback: int


class Callback(NamedTuple):
    id: int
    callable: Callable[..., None]


def _is_locked_method(method: Callable[..., Any]) -> bool:
    """@lock methods are serialized per object by the dispatch layer. The
    resolved callable is a MethodWrapperDispatcher whose .func is the raw
    function carrying the __lock__ marker; plain callables carry it directly.
    `is True` defends against mock auto-attributes in tests."""
    func = getattr(method, "func", method)
    return getattr(func, LOCK_ATTRIBUTE_NAME, False) is True


class _Peer:
    """One outbound connection: its own transport, its own lock and its own
    health state — a slow or black-holed peer stalls only its own senders,
    never traffic to healthy peers."""

    def __init__(self, transport: Transport):
        self.transport = transport
        self.lock = threading.Lock()
        self.missed_pongs = 0


class _ObjectLane:
    """A per-object FIFO for @lock methods: one worker thread executes them
    one at a time, in arrival order. A hung method stacks bounded queue
    entries here instead of pool workers."""

    def __init__(self, maxsize: int):
        self.queue: queue.Queue[tuple[Request, Callable[..., Any]] | None] = (
            queue.Queue(maxsize=maxsize)
        )
        self.closed = False
        self.thread: threading.Thread | None = None


class _Mailbox:
    """A single-waiter reply box for one in-flight request/ping."""

    def __init__(self, dst_bus: str):
        # dst_bus is recorded so a peer eviction can fail every request
        # pending on it
        self.dst_bus = dst_bus
        self.created = time.monotonic()
        self._queue: queue.SimpleQueue[Messages | None] = queue.SimpleQueue()

    def get(self, timeout: float | None = None) -> Messages | None:
        return self._queue.get(block=True, timeout=timeout)

    def put(self, message: Messages | None) -> None:
        self._queue.put(message)


class _Mailboxes:
    """Reply mailboxes keyed by request id.

    Responses are correlated to their caller by the id echoed in the
    Response/Pong, never by src URL, so concurrent calls sharing one src
    cannot receive each other's replies. Lifecycle: register before send,
    deliver by id, unregister when done. close_all() wakes every waiter
    with None exactly once — each mailbox has a single reader.
    """

    def __init__(self):
        self._boxes: dict[int, _Mailbox] = {}
        self._lock = threading.Lock()
        self._closed = False

    def register(self, key: int, dst_bus: str) -> _Mailbox:
        mailbox = _Mailbox(dst_bus)
        with self._lock:
            if self._closed:
                # bus is dead: the waiter wakes immediately with None
                mailbox.put(None)
                return mailbox
            self._boxes[key] = mailbox
        return mailbox

    def unregister(self, key: int) -> None:
        with self._lock:
            self._boxes.pop(key, None)

    def deliver(self, key: int, message: Messages) -> bool:
        with self._lock:
            mailbox = self._boxes.get(key)
        if mailbox is None:
            return False
        mailbox.put(message)
        return True

    def stats(self) -> list[dict[str, Any]]:
        """Pending mailboxes as JSON-safe entries, ages in seconds."""
        now = time.monotonic()
        with self._lock:
            return [
                {"id": key, "dst_bus": box.dst_bus, "age": now - box.created}
                for key, box in self._boxes.items()
            ]

    def fail_peer(self, dst_bus: str) -> None:
        """Wake every request pending on dst_bus with None: the peer is gone
        and its replies will never arrive."""
        with self._lock:
            keys = [key for key, box in self._boxes.items() if box.dst_bus == dst_bus]
            boxes = [self._boxes.pop(key) for key in keys]
        for mailbox in boxes:
            mailbox.put(None)

    def close_all(self) -> None:
        with self._lock:
            self._closed = True
            boxes = list(self._boxes.values())
            self._boxes.clear()
        for mailbox in boxes:
            mailbox.put(None)


class Bus:
    def __init__(
        self,
        url: str,
        *,
        handler_pool_size: int = 64,
        control_pool_size: int = 16,
        lane_queue_size: int = 32,
        lane_idle_timeout: float = 60.0,
        health_interval: float = 30.0,
        health_timeout: float = 2.0,
    ):
        self.url = create_url(url, cls="Bus")

        # tiered dispatch: requests and event callbacks (arbitrary user code,
        # can block) run on the bounded handler pool; pings and publish
        # fan-out (small, framework-only work that still touches sockets) run
        # on their own control pool so a wedged handler pool can never starve
        # liveness checks or event distribution
        self._handler_pool = ThreadPoolExecutor(
            max_workers=handler_pool_size,
            thread_name_prefix=f"chimera-bus-handler-{self.url.port}",
        )
        self._control_pool = ThreadPoolExecutor(
            max_workers=control_pool_size,
            thread_name_prefix=f"chimera-bus-control-{self.url.port}",
        )

        self._running = threading.Event()
        self._bus_started = threading.Event()

        # always-available waker for the selector loop: exists from birth so
        # shutdown can signal no matter when it happens (no start/stop window)
        self._waker_r, self._waker_w = os.pipe()

        # shutdown()/teardown are idempotent and race-safe
        self._shutdown_lock = threading.Lock()
        self._shutdown_done = threading.Event()
        self._teardown_claimed = threading.Event()
        self._teardown_finished = threading.Event()

        # per-object FIFO lanes for @lock methods
        self._lanes: dict[str, _ObjectLane] = {}
        self._lanes_lock = threading.Lock()
        self._lane_queue_size = lane_queue_size
        self._lane_idle_timeout = lane_idle_timeout

        # inbound messages to be dispatched by _process_queue
        self._inbox: queue.SimpleQueue[Messages | None] = queue.SimpleQueue()

        # reply mailboxes for in-flight requests/pings, keyed by request id
        self._mailboxes = _Mailboxes()

        # callbacks represent the subscriber-side of the pubsub model, where we can have references to the callbacks
        self._callbacks: dict[EventId, dict[Subscriber, Callback]] = {}

        # subscribers represent the publisher-side of the pubsub model, where we don't have references to the callbacks
        self._subscribers: dict[EventId, set[Subscriber]] = {}

        # client-side map from what the user subscribed to the wire token,
        # keyed by (pub, event): unsubscribe finds the entry by callable
        # equality (==) and takes the subscriber identity from the entry, so
        # it works whichever proxy or object made the subscription
        self._subscriptions: dict[
            tuple[str, str], list[tuple[URL, Callable[..., None], int]]
        ] = {}

        self._pubsub_lock = threading.Lock()

        self._inbound: Transport = create_transport(self.url.bus)
        self._inbound.bind()

        # outbound peers, one connection each; the map lock guards only the
        # map — dialing and sending happen under each peer's own lock
        self._peers: dict[str, _Peer] = {}
        self._peers_lock = threading.Lock()

        # health check: the backstop for silent partitions that never emit a
        # pipe-removal event (no FIN/RST — pipe eviction cannot see those)
        self._health_interval = health_interval
        self._health_timeout = health_timeout

        self._encoder = msgspec.json.Encoder()
        self._decoder = msgspec.json.Decoder(Messages)

    def _wake_selector(self) -> None:
        try:
            os.write(self._waker_w, b"\0")
        except OSError:
            # waker already closed by teardown: the loop is gone anyway
            pass

    def shutdown(self):
        with self._shutdown_lock:
            if self._shutdown_done.is_set():
                return
            self._shutdown_done.set()

        # signal: stop the loop, wake every pending request/ping with None
        # (single reader each) and stop the dispatch thread
        self._running.clear()
        self._wake_selector()
        self._mailboxes.close_all()
        self._inbox.put(None)

        if self._bus_started.is_set():
            # the selector-loop thread owns teardown on its way out; wait for
            # it unless waiting would deadlock (we are that thread, or a pool
            # worker the teardown itself joins)
            current = threading.current_thread()
            if current is not getattr(self, "_loop_thread", None) and (
                not self._is_own_worker()
            ):
                self._teardown_finished.wait(timeout=5)
        else:
            # the bus never ran: there is no loop thread to do it
            self._teardown()

    def _teardown(self):
        """Release every resource, exactly once. Runs on the selector-loop
        thread's way out, or directly from shutdown() when the bus never
        started."""
        with self._shutdown_lock:
            if self._teardown_claimed.is_set():
                return
            self._teardown_claimed.set()

        # make sure the helper threads are signalled even when teardown is
        # entered without shutdown() (loop crash, ctrl-c)
        self._shutdown_done.set()
        self._running.clear()
        self._mailboxes.close_all()
        self._inbox.put(None)

        dispatch = getattr(self, "_dispatch_thread", None)
        if dispatch is not None and dispatch is not threading.current_thread():
            dispatch.join(timeout=5)

        health = getattr(self, "_health_thread", None)
        if health is not None and health is not threading.current_thread():
            health.join(timeout=5)

        # stop the lanes: a sentinel wakes each worker; short join only —
        # they are daemon threads, so a truly hung instrument method cannot
        # block the interpreter from exiting
        with self._lanes_lock:
            lanes = list(self._lanes.values())
            self._lanes.clear()
            for lane in lanes:
                lane.closed = True
        for lane in lanes:
            try:
                lane.queue.put_nowait(None)
            except queue.Full:
                pass
        for lane in lanes:
            if (
                lane.thread is not None
                and lane.thread is not threading.current_thread()
            ):
                lane.thread.join(timeout=1)

        # a pool worker asking for teardown must not join its own pool;
        # queued handler work is cancelled (their done-callbacks see
        # CancelledError), queued control work is small and drains
        current = threading.current_thread()
        self._handler_pool.shutdown(
            wait=current not in self._handler_pool._threads, cancel_futures=True
        )
        self._control_pool.shutdown(wait=current not in self._control_pool._threads)

        self._inbound.close()
        for fd in (self._waker_w, self._waker_r):
            try:
                os.close(fd)
            except OSError:
                pass

        # snapshot under the lock: a concurrent peer eviction may still
        # mutate the map while we tear down
        with self._peers_lock:
            outbound = [peer.transport for peer in self._peers.values()]
            self._peers.clear()
        for socket in outbound:
            socket.close()

        self._teardown_finished.set()

    def is_dead(self) -> bool:
        return self._shutdown_done.is_set() or (
            self._bus_started.is_set() and self._running.is_set() is False
        )

    def _is_own_worker(self) -> bool:
        current = threading.current_thread()
        return (
            current in self._handler_pool._threads
            or current in self._control_pool._threads
        )

    def stats(self) -> dict[str, Any]:
        """A read-only, JSON-serializable snapshot of the bus internals, for
        observability (chimera-ctl status)."""
        with self._pubsub_lock:
            subscribers = [
                {
                    "publisher": event_id.publisher,
                    "event": event_id.event,
                    "subscribers": len(subs),
                }
                for event_id, subs in self._subscribers.items()
            ]
            callbacks = [
                {
                    "publisher": event_id.publisher,
                    "event": event_id.event,
                    "callbacks": len(cbs),
                }
                for event_id, cbs in self._callbacks.items()
            ]

        with self._peers_lock:
            peers = list(self._peers.keys())

        with self._lanes_lock:
            lanes = [
                {
                    "path": path,
                    "queued": lane.queue.qsize(),
                    "alive": lane.thread.is_alive() if lane.thread else False,
                    "id": lane.thread.native_id if lane.thread else None,
                }
                for path, lane in self._lanes.items()
            ]

        return {
            "url": self.url.url,
            # the address peers see us as (dst_bus of messages we send)
            "inbox_url": self.url.bus,
            "running": self._running.is_set(),
            "started": self._bus_started.is_set(),
            "inbox_size": self._inbox.qsize(),
            "mailboxes": self._mailboxes.stats(),
            "peers": peers,
            "subscribers": subscribers,
            "callbacks": callbacks,
            "handler_pool": pool_stats(self._handler_pool),
            "control_pool": pool_stats(self._control_pool),
            "lanes": lanes,
        }

    def __del__(self):
        self.shutdown()

    def _cleanup_dead_subscribers(self, bus_url: str) -> None:
        with self._pubsub_lock:
            # Iterate through all events and remove subscribers from the dead bus
            for event_id in list(self._subscribers.keys()):
                dead_subscribers = {
                    sub
                    for sub in self._subscribers[event_id]
                    if sub.subscriber.bus == bus_url
                }
                for sub in dead_subscribers:
                    self._subscribers[event_id].discard(sub)
                    # Also clean up from callbacks if this is our local bus
                    if event_id in self._callbacks and sub in self._callbacks[event_id]:
                        del self._callbacks[event_id][sub]

                # Clean up empty event_ids
                if not self._subscribers[event_id]:
                    del self._subscribers[event_id]
                if event_id in self._callbacks and not self._callbacks[event_id]:
                    del self._callbacks[event_id]

        log.debug(f"bus: cleaned up subscribers from dead bus: {bus_url}")

    def _ping_peer(self, dst_bus: str) -> bool:
        """True if the peer answered anything at all within the health
        timeout — even a not-found Pong proves the bus over there is alive."""
        ping = Protocol.ping(src=self.url.url, dst=f"{dst_bus}{MANAGER_LOCATION}")
        mailbox = self._mailboxes.register(ping.id, ping.dst_bus)
        try:
            if not self._push(ping):
                return False
            try:
                return mailbox.get(timeout=self._health_timeout) is not None
            except queue.Empty:
                return False
        finally:
            self._mailboxes.unregister(ping.id)

    def _health_check_once(self) -> None:
        with self._peers_lock:
            peers = dict(self._peers)

        for dst_bus, peer in peers.items():
            if self._ping_peer(dst_bus):
                peer.missed_pongs = 0
                continue

            peer.missed_pongs += 1
            log.warning(
                f"bus: peer {dst_bus} missed pong "
                f"({peer.missed_pongs}/{_MAX_MISSED_PONGS})"
            )
            if peer.missed_pongs >= _MAX_MISSED_PONGS:
                log.warning(f"bus: peer {dst_bus} unresponsive, evicting")
                self._evict_peer(dst_bus)

    def _health_loop(self) -> None:
        while not self._shutdown_done.wait(self._health_interval):
            try:
                self._health_check_once()
            except Exception:
                log.exception("bus: health check failed")

    def _schedule_peer_eviction(self, dst_bus: str) -> None:
        # called from a transport worker thread on connection loss: hand off
        # immediately, socket operations are not allowed in that context
        if self.is_dead():
            return
        try:
            # eviction is control work: it must run even when handlers are wedged
            self._control_pool.submit(self._evict_peer, dst_bus)
        except RuntimeError:
            # pool already shut down: the bus is going away anyway
            pass

    def _evict_peer(self, dst_bus: str) -> None:
        """A peer connection was lost: drop the outbound link, its
        subscriptions and every request still waiting on it. The peer
        reconnects implicitly on the next send to it (and reconnecting
        subscribers must re-subscribe)."""
        with self._peers_lock:
            peer = self._peers.pop(dst_bus, None)

        if peer is None:
            # already evicted, or racing our own shutdown
            return

        log.debug(f"bus: peer disconnected, evicting: {dst_bus}")
        peer.transport.close()
        self._cleanup_dead_subscribers(dst_bus)
        self._mailboxes.fail_peer(dst_bus)

    def _push(self, message: Messages) -> bool:
        """Hand a message to its destination. Returns False only when the
        message definitively could not be delivered (dead bus, connect or
        encode failure, dead socket); backpressure drops still return True —
        the peer is alive and a caller timeout covers the loss."""
        if self.is_dead():
            log.warning("push failed, bus is dead, not accepting new messages")
            return False

        if message.dst_bus == self.url.bus:
            # NOTE: we don't need to serialize/deserialize messages sent locally
            #       but we must check if they are serializable, otherwise code won't
            #       work when sending to remote buses.
            try:
                _ = self._encoder.encode(message)
            except Exception:
                log.exception(
                    f"bus: serialization issue, won't work on remote buses: {message}"
                )

            # FIXME: this could block if you send too much without receiving.
            if isinstance(message, Response) or isinstance(message, Pong):
                if not self._mailboxes.deliver(message.id, message):
                    # nobody is waiting: late reply after a timeout/unregister,
                    # or a stray id — drop it loudly, never resurrect a queue
                    log.debug(
                        f"bus: dropping {type(message).__name__} with no waiter "
                        f"(id={message.id}, src={message.src})"
                    )
            else:
                self._inbox.put(message)
            return True
        else:
            # encode outside every lock
            try:
                message_bytes = self._encoder.encode(message)
            except Exception:
                log.exception(f"bus: failed to encode message: {message}")
                return False

            peer = self._get_peer(message.dst_bus)
            if peer is None:
                return False

            with peer.lock:
                result = peer.transport.send(message_bytes)
                if result is SendResult.AGAIN:
                    # backpressure beyond the socket buffer: a short bounded
                    # retry absorbs sustained bursts; only this peer's
                    # senders wait
                    for _ in range(3):
                        time.sleep(0.01)
                        result = peer.transport.send(message_bytes)
                        if result is not SendResult.AGAIN:
                            break

            match result:
                case SendResult.OK:
                    return True
                case SendResult.AGAIN:
                    # still full: drop this message but never evict — a slow
                    # peer is not a dead one
                    log.warning(
                        f"bus: send buffer full for {message.dst_bus}, "
                        f"dropping {type(message).__name__}"
                    )
                    return True
                case SendResult.DEAD:
                    # if the peer is really gone the transport will notify
                    # us and _evict_peer does the cleanup
                    log.warning(
                        f"bus: send failed to {message.dst_bus}, "
                        f"dropping {type(message).__name__}"
                    )
                    return False

    def _get_peer(self, dst_bus: str) -> _Peer | None:
        with self._peers_lock:
            peer = self._peers.get(dst_bus)
        if peer is not None:
            return peer

        # dial outside the map lock: a black-holed peer blocking in connect
        # must not freeze senders to healthy peers (H1)
        # TODO: define some policy to handle closing of these sockets when not in use
        transport = create_transport(dst_bus)
        # peer loss is detected by the transport (pipe removal) and handled
        # off the transport thread; the send path itself never evicts
        transport.on_disconnect = lambda: self._schedule_peer_eviction(dst_bus)
        try:
            transport.connect()
        except Exception:
            log.exception(f"bus: failed to connect to outbound bus: {dst_bus}")
            # nothing stored: the next push retries the dial
            return None

        with self._peers_lock:
            existing = self._peers.get(dst_bus)
            if existing is not None:
                # lost a connect race: keep the winner's connection
                transport.close()
                return existing
            peer = _Peer(transport)
            self._peers[dst_bus] = peer
            return peer

    def _pop(self, /, timeout: float | None = None) -> Messages | None:
        message = self._inbox.get(block=True, timeout=timeout)
        if message is None:
            # None is the shutdown poison pill: re-circulate it so every other
            # reader blocked on the inbox wakes too, whatever the wake order
            self._inbox.put(None)
        return message

    def run_forever(self):
        try:
            self._run()
            log.info("bye...")
        except KeyboardInterrupt:
            log.info("ctrl-c: exiting...")
        except Exception:
            log.exception("bus error")
        finally:
            self.shutdown()

    def _run(self):
        self._loop_thread = threading.current_thread()

        selector = selectors.DefaultSelector()
        try:
            selector.register(self._inbound.recv_fd(), selectors.EVENT_READ)
            selector.register(self._waker_r, selectors.EVENT_READ)

            self._running.set()

            self._dispatch_thread = threading.Thread(
                target=self._process_queue,
                name=f"chimera-bus-dispatch-{self.url.port}",
                daemon=True,
            )
            self._dispatch_thread.start()

            self._health_thread = threading.Thread(
                target=self._health_loop,
                name=f"chimera-bus-health-{self.url.port}",
                daemon=True,
            )
            self._health_thread.start()

            self._bus_started.set()

            self._run_loop(selector)
        finally:
            selector.close()
            # this thread owns resource teardown: it is the only one that
            # knows the selector is no longer using the sockets and fds
            self._teardown()

    def _run_loop(self, selector: selectors.BaseSelector) -> None:
        while self._running.is_set():
            events = selector.select(timeout=None)
            if not events:
                log.warning("bus: selector returned no events")
                # Do spurious events happen? unprobably, but just in case...
                continue

            shutdown_requested = any([key.fd == self._waker_r for key, _ in events])
            if shutdown_requested:
                os.read(self._waker_r, 4096)
                log.debug("bus: shutdown requested")
                return

            new_messages = any([key.fd == self._inbound.recv_fd() for key, _ in events])
            if new_messages:
                # drain until empty: one fd readiness event can cover many queued
                # messages, and a spurious wakeup (no message at all) must not
                # crash the loop — recv() returns None in both cases
                while (recv_bytes := self._inbound.recv()) is not None:
                    # FIXME: this could fail, check and push back errors if needed.
                    try:
                        message: Messages = self._decoder.decode(recv_bytes)
                    except msgspec.DecodeError:
                        log.exception(f"bus: failed to decode message: {recv_bytes}")
                        continue

                    # FIXME: check for simple mistakes, like messages to the wrong receiver
                    self._push(message)

    #
    # bus client API
    #
    def ping(
        self,
        *,
        src: str | URL,
        dst: str | URL,
        timeout: float = 5.0,
    ) -> None | Pong:
        ping = Protocol.ping(
            src=parse_url(src).url,
            dst=parse_url(dst).url,
        )

        mailbox = self._mailboxes.register(ping.id, ping.dst_bus)
        try:
            self._push(ping)

            try:
                response = mailbox.get(timeout=timeout)
            except queue.Empty:
                return ping.pong(ok=False)
            if response is None or not isinstance(response, Pong):
                return None

            return response
        finally:
            self._mailboxes.unregister(ping.id)

    def request(
        self,
        *,
        src: str | URL,
        dst: str | URL,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        # no default timeout: instrument operations (slew, expose, ...) can
        # legitimately take unbounded time; callers opt in per call or proxy
        timeout: float | None = None,
    ) -> Response:
        request = Protocol.request(
            src=parse_url(src).url,
            dst=parse_url(dst).url,
            method=method,
            args=args or [],
            kwargs=kwargs or {},
        )

        mailbox = self._mailboxes.register(request.id, request.dst_bus)
        try:
            if not self._push(request):
                raise BusDeadException(
                    f"cannot send request {method} to {request.dst}: "
                    "bus or peer is dead"
                )

            try:
                response = mailbox.get(timeout=timeout)
            except queue.Empty:
                raise RequestTimeoutException(
                    f"no response for {method} on {request.dst} after {timeout}s"
                ) from None

            if response is None or not isinstance(response, Response):
                raise BusDeadException(
                    f"bus died while waiting for {method} on {request.dst}"
                )

            return response
        finally:
            self._mailboxes.unregister(request.id)

    def subscribe(
        self,
        *,
        sub: str | URL,
        pub: str | URL,
        event: str,
        callback: Callable[..., None],
    ):
        pub_url = parse_url(pub)
        sub_url = parse_url(sub)
        event_id = EventId(pub_url.url, event)
        registry_key = (pub_url.url, event)

        with self._pubsub_lock:
            entries = self._subscriptions.setdefault(registry_key, [])
            if any(registered == callback for _, registered, _ in entries):
                # already subscribed: keep the original token, nothing to do
                return

            token = CallbackId.new()
            entries.append((sub_url, callback, token))

            # register the callback before pushing Subscribe: a publish racing
            # this subscription cannot fire into the registration gap (M6)
            subscriber = Subscriber(sub_url, token)
            self._callbacks.setdefault(event_id, {})[subscriber] = Callback(
                token, callback
            )

        self._push(
            Protocol.subscribe(
                sub=sub_url.url,
                pub=pub_url.url,
                event=event,
                callback=token,
            )
        )

    def unsubscribe(
        self,
        *,
        sub: str | URL,
        pub: str | URL,
        event: str,
        callback: Callable[..., None],
    ):
        pub_url = parse_url(pub)
        event_id = EventId(pub_url.url, event)
        registry_key = (pub_url.url, event)

        with self._pubsub_lock:
            found = None
            entries = self._subscriptions.get(registry_key, [])
            for index, (entry_sub, registered, registered_token) in enumerate(entries):
                # matched by ==: bound methods compare equal even though every
                # access creates a distinct object, and ProxyMethod equality
                # matches any handle to the same object+method — this is what
                # makes unsubscribe(self.on_x) and `p.event -= s.clbk` work
                if registered == callback:
                    found = (entry_sub, registered_token)
                    del entries[index]
                    break

            if found is None:
                log.debug(f"unsubscribe: no subscription for {event} matches")
                return

            if not entries:
                del self._subscriptions[registry_key]

            entry_sub, token = found
            subscriber = Subscriber(entry_sub, token)
            event_callbacks = self._callbacks.get(event_id)
            if event_callbacks is not None:
                event_callbacks.pop(subscriber, None)
                if not event_callbacks:
                    del self._callbacks[event_id]

        self._push(
            Protocol.unsubscribe(
                sub=entry_sub.url,
                pub=pub_url.url,
                event=event,
                callback=token,
            )
        )

    def publish(
        self,
        *,
        pub: str,
        event: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        # TODO: should we return something to confirm delivery?
        self._push(
            Protocol.publish(
                pub=pub,
                event=event,
                args=args or [],
                kwargs=kwargs or {},
            )
        )

    #
    # bus server-side handling
    #
    def _process_queue(self):
        try:
            while self._running.is_set():
                message = self._pop()
                if message is None:
                    break

                match message:
                    # table-only ops run inline: nothing here may block
                    # (no _push, no user code), so they are structurally
                    # immune to pool starvation
                    case Subscribe():
                        self._handle_subscribe(message)
                    case Unsubscribe():
                        self._handle_unsubscribe(message)
                    case Ping():
                        _ = self._control_pool.submit(self._handle_ping, message)
                    case Publish():
                        _ = self._control_pool.submit(self._handle_publish, message)
                    case Request():
                        # routed inline (resolve + pick a lane/pool); the
                        # actual execution never happens on this thread
                        self._route_request(message)
                    case Event():
                        _ = self._handler_pool.submit(self._handle_event, message)
                    case _:
                        log.warning(f"Invalid message type: {type(message)}")

                # TODO: handle invalid request
                # self.transport.send(Protocol.error("Invalid request"))
        except Exception:
            log.exception("Error processing queue")
        finally:
            # signal only — never call shutdown() from this thread: teardown
            # joins us and pool.shutdown() could self-join
            self._running.clear()
            self._wake_selector()

    def resolve_request(
        self, object: str, method: str
    ) -> tuple[str | None, Callable[..., Any] | None]:
        return None, None

    def _route_request(self, request: Request) -> None:
        """Runs inline on the dispatch thread: resolve and route, never
        execute. Resolution is a dict lookup (framework code, microseconds);
        routing must not depend on the handler pool, or a wedged pool would
        starve the locked-method lanes it feeds."""
        try:
            dst = parse_url(request.dst)

            # FIXME: this should return a full url/path so we can send it back to the caller saying exactly who handled the request
            resource, method = self.resolve_request(dst.path, request.method)

            if not resource:
                self._control_pool.submit(
                    self._push, request.not_found(f"'{dst.cls}' not found")
                )
                return

            if not method:
                self._control_pool.submit(
                    self._push,
                    request.not_found(f"'{dst.cls}.{request.method}' not found"),
                )
                return

            if _is_locked_method(method):
                self._enqueue_lane(resource, request, method)
            else:
                self._handler_pool.submit(self._execute_request, request, method)
        except Exception as e:
            log.exception("error routing request")
            self._control_pool.submit(self._push, request.error(e))

    def _execute_request(self, request: Request, method: Callable[..., Any]) -> None:
        try:
            try:
                result = method(*request.args, **request.kwargs)
                self._push(request.ok(result))
            except Exception as e:
                self._push(request.error(e))
        except Exception:
            log.exception("error executing request")

    def _enqueue_lane(
        self, resource: str, request: Request, method: Callable[..., Any]
    ) -> None:
        with self._lanes_lock:
            lane = self._lanes.get(resource)
            if lane is None or lane.closed:
                lane = _ObjectLane(self._lane_queue_size)
                lane.thread = threading.Thread(
                    target=self._lane_worker,
                    args=(resource, lane),
                    name=f"chimera-bus-lane-{self.url.port}{resource}",
                    daemon=True,
                )
                self._lanes[resource] = lane
                lane.thread.start()

            try:
                lane.queue.put_nowait((request, method))
                return
            except queue.Full:
                pass

        # outside the lock: the object is drowning, tell the caller now
        # instead of piling stale commands behind a stuck instrument
        log.warning(
            f"bus: lane full for {resource} ({self._lane_queue_size} pending), "
            f"rejecting {request.method}"
        )
        self._control_pool.submit(
            self._push,
            request.busy(f"{resource} busy: {self._lane_queue_size} requests pending"),
        )

    def _lane_worker(self, resource: str, lane: _ObjectLane) -> None:
        while True:
            try:
                item = lane.queue.get(timeout=self._lane_idle_timeout)
            except queue.Empty:
                # idle: evict the lane. Re-check under the lock — enqueue
                # holds it while putting, so nothing can slip in unseen
                with self._lanes_lock:
                    if not lane.queue.empty():
                        continue
                    lane.closed = True
                    if self._lanes.get(resource) is lane:
                        del self._lanes[resource]
                return

            if item is None:
                # shutdown sentinel
                return

            request, method = item
            self._execute_request(request, method)

    def callbacks(self, /, event_id: EventId) -> dict[Subscriber, Callback]:
        with self._pubsub_lock:
            return dict(self._callbacks.get(event_id, {}))

    def subscribers(self, /, event_id: EventId) -> set[Subscriber]:
        with self._pubsub_lock:
            return set(self._subscribers.get(event_id, ()))

    def _handle_ping(self, message: Ping) -> None:
        try:
            # resolve the dst URL and return the resolved URL in the pong
            dst_url = parse_url(message.dst)
            cls, method = self.resolve_request(dst_url.path, "get_location")
            if cls is not None and method is not None:
                resolved_url = method()
                pong = message.pong(ok=True, resolved_url=resolved_url)
                self._push(pong)
            else:
                self._push(message.pong(ok=False))
        except Exception:
            log.exception("error handling ping")
            # still answer: a reachable bus must never look silently
            # partitioned just because resolution raised (health checks
            # count any pong as proof of life)
            try:
                self._push(message.pong(ok=False))
            except Exception:
                pass

    def _handle_subscribe(self, message: Subscribe):
        try:
            with self._pubsub_lock:
                event_id = EventId(message.pub, message.event)
                subscriber = Subscriber(parse_url(message.sub), message.callback)
                self._subscribers.setdefault(event_id, set()).add(subscriber)
        except Exception:
            log.exception("error handling subscribe")

    def _handle_unsubscribe(self, message: Unsubscribe):
        try:
            with self._pubsub_lock:
                event_id = EventId(message.pub, message.event)
                subscriber = Subscriber(parse_url(message.sub), message.callback)

                subscribers = self._subscribers.get(event_id)
                if subscribers is not None:
                    subscribers.discard(subscriber)
                    if not subscribers:
                        del self._subscribers[event_id]
        except Exception:
            log.exception("error handling unsubscribe")

    def _handle_publish(self, message: Publish):
        try:
            event_id = EventId(message.pub, message.event)

            # snapshot under the lock: subscribe/unsubscribe mutate the set
            # concurrently and an unlocked iteration silently drops the event
            with self._pubsub_lock:
                subscribers = set(self._subscribers.get(event_id, ()))

            # no subscribers for this event
            if not subscribers:
                return

            # unique set of buses where we have subscribers
            urls = set([sub.subscriber.bus for sub in subscribers])

            for url in urls:
                event = message.callback(
                    dst=url,
                    event=message.event,
                    args=message.args,
                    kwargs=message.kwargs,
                )
                self._push(event)
        except Exception:
            log.exception("error handling publish")

    def _handle_event(self, event: Event) -> None:
        try:
            event_id = EventId(event.src, event.event)

            # snapshot under the lock (see _handle_publish)
            with self._pubsub_lock:
                callables = [
                    callback.callable
                    for callback in self._callbacks.get(event_id, {}).values()
                ]

            for callable in callables:
                # exceptions inside event handlers are invisible to the
                # publisher: observe them via a (free) done-callback instead
                # of burning a second pool task on it
                event_future = self._handler_pool.submit(
                    callable, *event.args, **event.kwargs
                )
                event_future.add_done_callback(self._log_event_result(event))
        except Exception:
            log.exception("error handling event")

    @staticmethod
    def _log_event_result(event: Event) -> Callable[[Future[Any]], None]:
        def check(future: Future[Any]) -> None:
            try:
                _ = future.result()
            except CancelledError:
                # shutdown cancelled callbacks still queued: not an error
                pass
            except Exception:
                log.exception(f"error in event handler: {event.event}")

        return check
