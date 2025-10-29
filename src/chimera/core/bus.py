import collections
import logging
import queue
import selectors
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Literal, NamedTuple, Self

import msgspec

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
from chimera.core.transport import Transport
from chimera.core.transport_factory import create_transport
from chimera.core.url import URL, parse_url

log = logging.getLogger(__name__)


type PublisherId = str
type SubscriberId = URL


class CallbackId(int):
    @classmethod
    def new(cls, callable: Callable[..., None]) -> Self:
        return cls(id(callable))


class EventId(NamedTuple):
    publisher: PublisherId
    event: str


@dataclass(frozen=True)
class Subscriber:
    subscriber: SubscriberId
    callback: CallbackId


class Callback(NamedTuple):
    id: CallbackId
    callable: Callable[..., None]


class Bus:
    def __init__(self, url: str):
        self.url = parse_url(f"{url}/Bus/{uuid.uuid4().hex}")

        self._pool = ThreadPoolExecutor()

        self._running = threading.Event()
        self._bus_started = threading.Event()

        self._q: dict[str, queue.SimpleQueue[Messages | None]] = (
            collections.defaultdict(queue.SimpleQueue)
        )

        # callbacks represent the subscriber-side of the pubsub model, where we can have references to the callbacks
        self._callbacks: collections.defaultdict[
            EventId, dict[Subscriber, Callback]
        ] = collections.defaultdict(dict)

        # subscribers represent the publisher-side of the pubsub model, where we don't have references to the callbacks
        self._subscribers: collections.defaultdict[EventId, set[Subscriber]] = (
            collections.defaultdict(set)
        )

        self._inbound: Transport = create_transport(self.url.bus)
        self._inbound.bind()

        self._outbound: dict[str, Transport] = {}

        self._encoder = msgspec.json.Encoder()
        self._decoder = msgspec.json.Decoder(Messages)

    def shutdown(self):
        if not self.is_dead():
            self._running.clear()

            shutdown = create_transport(f"inproc://{self.url.path}")
            shutdown.connect()
            shutdown.send(b"shutdown request")

            # signal all response queue handlers that we are shutting down
            for key in self._q.keys():
                # FIXME: why we need to send multiple Nones? only one fails to unblock some threads.
                # send a few Nones to unblock any pending gets
                for _ in range(5):
                    self._q[key].put(None)

            self._process_queue_future.result()
            self._pool.shutdown()

            self._inbound.close()
            self._internal.close()

            for socket in self._outbound.values():
                socket.close()

    def is_dead(self) -> bool:
        return self._bus_started.is_set() and self._running.is_set() is False

    def __del__(self):
        self.shutdown()

    def _push(self, message: Messages) -> None:
        if self.is_dead():
            log.warning("push failed, bus is dead, not accepting new messages")
            return

        if message.dst_bus == self.url.bus:
            # FIXME: this could block if you send too much without receiving.
            if isinstance(message, Response) or isinstance(message, Pong):
                self._q[message.dst].put(message)
            else:
                self._q[self.url.url].put(message)
        else:
            if message.dst_bus not in self._outbound:
                # TODO: define some policy to handle closing of these sockets when not in use
                self._outbound[message.dst_bus] = create_transport(message.dst_bus)
                # TODO: block or not?
                self._outbound[message.dst_bus].connect()

            # FIXME: serialization could fail, handle it
            self._outbound[message.dst_bus].send(self._encoder.encode(message))

    def _pop(
        self, /, key: str | None = None, timeout: float | None = None
    ) -> Messages | None:
        key = key or str(self.url)
        return self._q[key].get(block=True, timeout=timeout)

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
        self._internal = create_transport(f"inproc://{self.url.path}")
        self._internal.bind()

        selector = selectors.DefaultSelector()
        selector.register(self._inbound.fd(), selectors.EVENT_READ)
        selector.register(self._internal.fd(), selectors.EVENT_READ)

        self._running.set()

        self._process_queue_future: Future[None] = self._pool.submit(
            self._process_queue
        )

        self._bus_started.set()

        while self._running.is_set():
            events = selector.select(timeout=None)
            if not events:
                log.warning("bus: selector returned no events")
                # Do spurious events happen? unprobably, but just in case...
                continue

            shutdown_requested = any(
                [key.fd == self._internal.fd() for key, _ in events]
            )
            # NOTE: if asked for shutdown, the caller is already closing sockets, so we cannot
            #       handle anything more, so better exit here. If we implement a way to ack the
            #       shutdown request, we might be able to process in-progress messages and then exit
            if shutdown_requested:
                log.debug("bus: shutdown requested")
                return

            new_messages = any([key.fd == self._inbound.fd() for key, _ in events])
            if new_messages:
                recv_bytes = self._inbound.recv()

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

        self._push(ping)

        try:
            response = self._pop(ping.src)
        except queue.Empty:
            return ping.pong(ok=False)
        if response is None or not isinstance(response, Pong):
            return None

        return response

    # TODO: add timeout?
    def request(
        self,
        *,
        src: str | URL,
        dst: str | URL,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None | Response:
        request = Protocol.request(
            src=parse_url(src).url,
            dst=parse_url(dst).url,
            method=method,
            args=args or [],
            kwargs=kwargs or {},
        )

        self._push(request)

        response = self._pop(request.src)
        if response is None or not isinstance(response, Response):
            raise RuntimeError("bus is dead")

        return response

    def subscribe(
        self,
        *,
        sub: str | URL,
        pub: str | URL,
        event: str,
        callback: Callable[..., None],
    ):
        pub_url = parse_url(pub)

        callback_id = CallbackId.new(callback)
        subscriber = Subscriber(parse_url(sub), callback_id)
        event_id = EventId(pub_url.url, event)

        self._push(
            Protocol.subscribe(
                sub=parse_url(sub).url,
                pub=pub_url.url,
                event=event,
                callback=callback_id,
            )
        )

        self._callbacks[event_id][subscriber] = Callback(callback_id, callback)

    def unsubscribe(
        self,
        *,
        sub: str | URL,
        pub: str | URL,
        event: str,
        callback: Callable[..., None],
    ):
        pub_url = parse_url(pub)
        callback_id = CallbackId.new(callback)
        subscriber = Subscriber(parse_url(sub), callback_id)
        event_id = EventId(pub_url.url, event)

        self._push(
            Protocol.unsubscribe(
                sub=parse_url(sub).url,
                pub=pub_url.url,
                event=event,
                callback=callback_id,
            )
        )

        if subscriber in self._callbacks[event_id]:
            del self._callbacks[event_id][subscriber]

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
                    case Ping():
                        _ = self._pool.submit(self._handle_ping, message)
                    case Request():
                        _ = self._pool.submit(self._handle_request, message)
                    case Subscribe():
                        _ = self._pool.submit(self._handle_subscribe, message)
                    case Unsubscribe():
                        _ = self._pool.submit(self._handle_unsubscribe, message)
                    case Publish():
                        _ = self._pool.submit(self._handle_publish, message)
                    case Event():
                        _ = self._pool.submit(self._handle_event, message)
                    case _:
                        log.warning(f"Invalid message type: {type(message)}")

                # TODO: handle invalid request
                # self.transport.send(Protocol.error("Invalid request"))
        except Exception:
            log.exception("Error processing queue")
        finally:
            self.shutdown()

    def resolve_request(
        self, object: str, method: str
    ) -> tuple[bool, Literal[False] | Callable[..., Any]]:
        return False, False

    def _handle_request(self, request: Request) -> None:
        try:
            dst = parse_url(request.dst)

            # FIXME: this should return a full url/path so we can send it back to the caller saying exactly who handled the request
            resource, method = self.resolve_request(dst.path, request.method)

            if not resource:
                self._push(request.not_found(f"'{dst.cls}' not found"))
                return

            if not method:
                self._push(request.not_found(f"'{dst.cls}.{request.method}' not found"))
                return

            try:
                result = method(*request.args, **request.kwargs)
                self._push(request.ok(result))
            except Exception as e:
                self._push(request.error(e))
        except Exception:
            log.exception("error handling request")

    def callbacks(self, /, event_id: EventId) -> dict[Subscriber, Callback]:
        return self._callbacks[event_id]

    def subscribers(self, /, event_id: EventId) -> set[Subscriber]:
        return self._subscribers[event_id]

    def _handle_ping(self, message: Ping) -> None:
        try:
            self._push(message.pong())
        except Exception:
            log.exception("error handling subscribe")

    def _handle_subscribe(self, message: Subscribe):
        try:
            event_id = EventId(message.pub, message.event)
            subscriber = Subscriber(
                parse_url(message.sub), CallbackId(message.callback)
            )
            self._subscribers[event_id].add(subscriber)
        except Exception:
            log.exception("error handling subscribe")

    def _handle_unsubscribe(self, message: Unsubscribe):
        try:
            event_id = EventId(message.pub, message.event)
            subscriber = Subscriber(
                parse_url(message.sub), CallbackId(message.callback)
            )

            if subscriber in self._subscribers[event_id]:
                self._subscribers[event_id].remove(subscriber)
        except Exception:
            log.exception("error handling unsubscribe")

    def _handle_publish(self, message: Publish):
        try:
            event_id = EventId(message.pub, message.event)
            subscribers = self._subscribers[event_id]

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

            for callback in self._callbacks[event_id].values():
                method = callback.callable
                # FIXME: we cannot see exception happening inside the event handlers, implement
                #        something to call the futures and check for exceptions later
                self._pool.submit(method, *event.args, **event.kwargs)
        except Exception:
            log.exception("error handling event")
