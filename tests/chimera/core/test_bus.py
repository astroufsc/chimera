import threading
import time
from collections.abc import Callable, Generator
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any
from unittest.mock import MagicMock

import msgspec
import pytest

from chimera.core.bus import Bus, Callback, CallbackId, EventId, Subscriber
from chimera.core.protocol import Protocol
from chimera.core.transport import SendResult, Transport
from chimera.core.transport_factory import create_transport
from chimera.core.url import parse_url


def print_results(op: str, n: int, dt: float):
    ops = f"{op}/s"
    print(
        f"{op:20}[{n}] {dt:.6f}s {n / dt:.0f} {ops:<20} {(dt * 1_000_000 / n):.3f} μs/{op}"
    )


def fake_get_az() -> float:
    return 42.0


def fake_get_location() -> str:
    return "/FakeTelescope/fake"


def resolve_request(
    object: str, method: str
) -> tuple[str | None, Callable[..., Any] | None]:
    if object == "/Telescope/0" and method == "get_az":
        return "/FakeTelescope/fake", fake_get_az
    elif object == "/Telescope/0" and method == "get_location":
        return "/FakeTelescope/fake", fake_get_location
    elif object == "/Telescope/0" and method == "unknown_method":
        return "/FakeTelescope/fake", None
    return None, None


def ping_test(*, n: int, src_bus: Bus, dst_bus: Bus):
    print()

    src = f"{src_bus.url.bus}/Proxy/932032"
    dst = f"{dst_bus.url.bus}/Telescope/0"
    dst_not_found = f"{dst_bus.url.bus}/Camera/0"

    dst_bus.resolve_request = resolve_request

    def sender():
        t0 = time.monotonic()
        for _ in range(n):
            pong = src_bus.ping(src=src, dst=dst)
            assert (
                pong is not None
                and pong.ok is True
                and pong.resolved_url == "/FakeTelescope/fake"
            )
        print_results("ping ok", n, time.monotonic() - t0)

        t0 = time.monotonic()
        for _ in range(n):
            pong = src_bus.ping(src=src, dst=dst_not_found)
            assert pong is not None and pong.ok is False and pong.resolved_url is None
        print_results("ping not-found", n, time.monotonic() - t0)

    pool = ThreadPoolExecutor()
    dst_bus_future = pool.submit(dst_bus.run_forever)

    if src_bus.url != dst_bus.url:
        src_bus_future = pool.submit(src_bus.run_forever)
    else:
        src_bus_future = None

    sender_future = pool.submit(sender)

    sender_future.result()

    src_bus.shutdown()
    dst_bus.shutdown()

    dst_bus_future.result()
    if src_bus_future:
        src_bus_future.result()

    pool.shutdown()


def rpc_test(*, n: int, src_bus: Bus, dst_bus: Bus):
    print()

    dst = f"{dst_bus.url.bus}/Telescope/0"
    src = f"{src_bus.url.bus}/Proxy/0"

    src_not_found = f"{src_bus.url.bus}/Proxy/1"
    dst_not_found = f"{dst_bus.url.bus}/Telescope/not-found"

    dst_bus.resolve_request = resolve_request

    def caller_ok():
        t0 = time.monotonic()
        for _ in range(n):
            response = src_bus.request(src=src, dst=dst, method="get_az")
            assert response is not None
            assert response.result == 42.0
            assert response.code == 200
            assert response.error is None
        print_results("rpc-ok", n, time.monotonic() - t0)

    def caller_resource_not_found():
        t0 = time.monotonic()
        for _ in range(n):
            response = src_bus.request(
                src=src_not_found, dst=dst_not_found, method="get_az"
            )
            assert response is not None
            assert response.result is None
            assert response.code == 404
            assert response.error is not None
            assert "not found" in response.error

        print_results("rpc-res-not-found", n, time.monotonic() - t0)

    pool = ThreadPoolExecutor()
    caller_ok_future = pool.submit(caller_ok)
    caller_resource_not_found_future = pool.submit(caller_resource_not_found)

    dst_bus_future = pool.submit(dst_bus.run_forever)
    if src_bus.url != dst_bus.url:
        src_bus_future = pool.submit(src_bus.run_forever)
    else:
        src_bus_future = None

    caller_ok_future.result()
    caller_resource_not_found_future.result()

    src_bus.shutdown()
    dst_bus.shutdown()

    dst_bus_future.result()
    if src_bus_future:
        src_bus_future.result()

    pool.shutdown()


def pubsub_test(*, n_subscribers: int, n_events: int, src_bus: Bus, dst_bus: Bus):
    print()

    sub = [f"{src_bus.url.bus}/Proxy/{i}" for i in range(n_subscribers)]
    pub = f"{dst_bus.url.bus}/Telescope/0"

    def create_callback(i: int):
        def on_slew_begin(ra: float, dec: float, slew_status: str):
            # NOTE: we cannot assert exact values because we cannot guarantee event ordering
            assert ra >= 42.0 and ra < 42.0 + n_events
            assert dec >= 50.0 and dec < 50.0 + n_events
            assert slew_status == "complete"

        return MagicMock(side_effect=on_slew_begin)

    callbacks = [create_callback(i) for i in range(n_subscribers)]
    assert len(set([id(cb) for cb in callbacks])) == n_subscribers, (
        "callbacks must be unique"
    )

    event = "slew_begin"

    def subscribe():
        t0 = time.monotonic()
        for i in range(n_subscribers):
            # subscribe twice to test duplicate handling
            src_bus.subscribe(sub=sub[i], pub=pub, event=event, callback=callbacks[i])
            src_bus.subscribe(sub=sub[i], pub=pub, event=event, callback=callbacks[i])
        print_results("sub", n_subscribers, time.monotonic() - t0)

        # check subscriber-side callback registrations
        event_id = EventId(pub, event)

        assert len(src_bus.callbacks(event_id)) == n_subscribers

        for i in range(n_subscribers):
            callback_id = CallbackId.new(callbacks[i])
            callback = Callback(callback_id, callbacks[i])
            subscriber = Subscriber(parse_url(sub[i]), callback_id)

            # for a given event and callback, only one subscription was created, even if tried twice
            assert src_bus.callbacks(event_id)[subscriber] == callback

        time.sleep(0.5)  # give some time for subscriptions to propagate

        # check publisher-side subscriber registrations
        assert len(dst_bus.subscribers(event_id)) == n_subscribers

        for i in range(n_subscribers):
            callback_id = CallbackId.new(callbacks[i])
            callback = Callback(callback_id, callbacks[i])
            subscriber = Subscriber(parse_url(sub[i]), callback_id)

            subscribers = dst_bus.subscribers(event_id)
            assert subscriber in subscribers
            our_subscriber = [sub for sub in subscribers if sub == subscriber][0]
            assert our_subscriber.subscriber == parse_url(sub[i])
            assert our_subscriber.callback == subscriber.callback

    def unsubscribe():
        t0 = time.monotonic()
        for i in range(n_subscribers):
            # unsubscribe twice to test idempotency
            src_bus.unsubscribe(sub=sub[i], pub=pub, event=event, callback=callbacks[i])
            src_bus.unsubscribe(sub=sub[i], pub=pub, event=event, callback=callbacks[i])
        print_results("unsub", n_subscribers, time.monotonic() - t0)

        # check client-side callback unregistrations
        event_id = EventId(pub, event)

        for i in range(n_subscribers):
            assert len(src_bus.callbacks(event_id)) == 0

        time.sleep(0.5)  # give some time for unsubscriptions to propagate

        # check server-side subscriber unregistrations
        assert len(dst_bus.subscribers(event_id)) == 0

    def publish():
        t0 = time.monotonic()
        for i in range(n_events):
            dst_bus.publish(
                pub=pub,
                event=event,
                args=[42.0 + i, 50.0 + i],
                kwargs={"slew_status": "complete"},
            )
        print_results("pub", n_events, time.monotonic() - t0)

        # give some time for events to be generated and processed
        # for each published event, all subscribers should receive and event
        time.sleep(1.0)

        for i in range(n_subscribers):
            assert callbacks[i].call_count == n_events

    pool = ThreadPoolExecutor()

    dst_bus_future = pool.submit(dst_bus.run_forever)
    if src_bus.url != dst_bus.url:
        src_bus_future = pool.submit(src_bus.run_forever)
    else:
        src_bus_future = None

    subscribe_future = pool.submit(subscribe)
    subscribe_future.result()

    publish_future = pool.submit(publish)
    publish_future.result()

    unsubscribe_future = pool.submit(unsubscribe)
    unsubscribe_future.result()

    src_bus.shutdown()
    dst_bus.shutdown()

    dst_bus_future.result()
    if src_bus_future:
        src_bus_future.result()

    pool.shutdown()


@pytest.fixture
def create_bus() -> Generator[Callable[[str], Bus]]:
    buses: list[Bus] = []

    def _wrapper(url: str) -> Bus:
        bus = Bus(url)
        buses.append(bus)
        return bus

    yield _wrapper

    for bus in buses:
        bus.shutdown()


def test_ping_local(create_bus: Callable[[str], Bus]):
    bus = create_bus("tcp://127.0.0.1:2000")
    ping_test(n=50_000, src_bus=bus, dst_bus=bus)


def test_ping_remote(create_bus: Callable[[str], Bus]):
    my_bus = create_bus("tcp://127.0.0.1:2001")
    other_bus = create_bus("tcp://127.0.0.1:2002")
    ping_test(n=10_000, src_bus=my_bus, dst_bus=other_bus)


def test_rpc_local(create_bus: Callable[[str], Bus]):
    bus = create_bus("tcp://127.0.0.1:3000")
    rpc_test(n=10_000, src_bus=bus, dst_bus=bus)


def test_rpc_remote(create_bus: Callable[[str], Bus]):
    my_bus = create_bus("tcp://127.0.0.1:3001")
    other_bus = create_bus("tcp://127.0.0.1:3002")
    rpc_test(n=2_000, src_bus=my_bus, dst_bus=other_bus)


def test_pubsub_local(create_bus: Callable[[str], Bus]):
    bus = create_bus("tcp://127.0.0.1:4000")
    pubsub_test(n_subscribers=2, n_events=2, src_bus=bus, dst_bus=bus)


def test_pubsub_remote(create_bus: Callable[[str], Bus]):
    my_bus = create_bus("tcp://127.0.0.1:4001")
    other_bus = create_bus("tcp://127.0.0.1:4002")
    pubsub_test(n_subscribers=2, n_events=1_000, src_bus=my_bus, dst_bus=other_bus)


#
# transport hardening: recv drain + backpressure classification
#


class AlwaysAgainTransport(Transport):
    """A transport whose peer never drains its buffer: every send is backpressure."""

    def __init__(self, url: str):
        super().__init__(url)
        self.send_count = 0

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, data: bytes) -> SendResult:
        self.send_count += 1
        return SendResult.AGAIN


def test_transport_recv_empty_returns_none():
    transport = create_transport("tcp://127.0.0.1:15001")
    transport.bind()
    try:
        # fd not readable and no message queued: must not raise (spurious wakeup)
        assert transport.recv() is None
    finally:
        transport.close()


def test_transport_closed_is_safe():
    transport = create_transport("tcp://127.0.0.1:15002")
    transport.bind()
    transport.close()
    transport.close()  # idempotent
    assert transport.send(b"data") is SendResult.DEAD
    assert transport.recv() is None


def test_recv_burst_drained(create_bus: Callable[[str], Bus]):
    """One selector readiness event can cover many queued messages; the recv
    drain loop must process all of them."""
    src_bus = create_bus("tcp://127.0.0.1:15003")
    dst_bus = create_bus("tcp://127.0.0.1:15004")

    n = 200
    received: list[int] = []
    received_lock = threading.Lock()
    done = threading.Event()

    def poke(i: int) -> int:
        with received_lock:
            received.append(i)
            if len(received) == n:
                done.set()
        return i

    dst_bus.resolve_request = lambda object, method: ("/Fake/0", poke)

    pool = ThreadPoolExecutor()
    dst_future = pool.submit(dst_bus.run_forever)
    src_future = pool.submit(src_bus.run_forever)
    assert dst_bus._bus_started.wait(5)
    assert src_bus._bus_started.wait(5)

    # burst messages over the wire as fast as the buffers accept them, retrying
    # on backpressure at the test level so all n arrive
    sender = create_transport(dst_bus.url.bus)
    sender.connect()
    encoder = msgspec.json.Encoder()
    try:
        for i in range(n):
            request = Protocol.request(
                src=f"{src_bus.url.bus}/Proxy/0",
                dst=f"{dst_bus.url.bus}/Fake/0",
                method="poke",
                args=[i],
            )
            data = encoder.encode(request)
            deadline = time.monotonic() + 5
            while sender.send(data) is not SendResult.OK:
                assert time.monotonic() < deadline, f"send of message {i} stuck"
                time.sleep(0.001)

        assert done.wait(10), f"only {len(received)}/{n} messages processed"
    finally:
        sender.close()

    src_bus.shutdown()
    dst_bus.shutdown()
    dst_future.result()
    src_future.result()
    pool.shutdown()


def test_backpressure_does_not_evict_subscribers(create_bus: Callable[[str], Bus]):
    """TryAgain means the peer is alive but slow: repeated backpressure must not
    close the connection nor destroy the peer's subscriptions."""
    bus = create_bus("tcp://127.0.0.1:15005")
    remote_bus = parse_url("tcp://127.0.0.1:15006/Proxy/0").bus

    pub = f"{bus.url.bus}/Telescope/0"
    event = "slew_begin"
    event_id = EventId(pub, event)

    # a remote subscriber, registered as if its Subscribe arrived over the wire
    bus._handle_subscribe(
        Protocol.subscribe(
            sub=f"{remote_bus}/Proxy/0", pub=pub, event=event, callback=1234
        )
    )

    # events to the remote bus will hit a full send buffer every time
    fake = AlwaysAgainTransport(remote_bus)
    bus._outbound[remote_bus] = fake

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    n = 5  # > _max_send_failures, so miscounting backpressure would evict
    for i in range(n):
        bus.publish(pub=pub, event=event, args=[i], kwargs={})

    deadline = time.monotonic() + 5
    while fake.send_count < n:
        assert time.monotonic() < deadline, (
            f"only {fake.send_count}/{n} sends attempted"
        )
        time.sleep(0.01)

    assert remote_bus in bus._outbound
    assert len(bus.subscribers(event_id)) == 1
    assert bus._outbound_failures[remote_bus] == 0

    bus.shutdown()
    bus_future.result()
    pool.shutdown()
