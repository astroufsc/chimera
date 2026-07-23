import logging
import os
import threading
import time
from collections.abc import Callable, Generator
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any
from unittest.mock import MagicMock

import msgspec
import pytest

from chimera.core.bus import Bus, EventId, _Peer
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import (
    BusDeadException,
    ObjectBusyException,
    RequestTimeoutException,
)
from chimera.core.lock import lock
from chimera.core.manager import Manager
from chimera.core.protocol import Protocol, Subscribe
from chimera.core.proxy import Proxy
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

        registered = src_bus.callbacks(event_id)
        assert len(registered) == n_subscribers

        # for a given event and callback, only one subscription was created,
        # even if tried twice; callables are matched by ==
        registered_callables = [callback.callable for callback in registered.values()]
        for i in range(n_subscribers):
            assert registered_callables.count(callbacks[i]) == 1

        time.sleep(0.5)  # give some time for subscriptions to propagate

        # check publisher-side subscriber registrations: same tokens and
        # subscriber urls as the client side
        subscribers = dst_bus.subscribers(event_id)
        assert len(subscribers) == n_subscribers
        assert {s.callback for s in subscribers} == {
            callback.id for callback in registered.values()
        }
        assert {s.subscriber for s in subscribers} == {parse_url(u) for u in sub}

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
def create_bus() -> Generator[Callable[..., Bus]]:
    buses: list[Bus] = []

    def _wrapper(url: str, **kwargs: Any) -> Bus:
        bus = Bus(url, **kwargs)
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


class AlwaysDeadTransport(AlwaysAgainTransport):
    """A transport whose sends always fail terminally."""

    def send(self, data: bytes) -> SendResult:
        self.send_count += 1
        return SendResult.DEAD


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
    bus._peers[remote_bus] = _Peer(fake)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    n = 5
    for i in range(n):
        bus.publish(pub=pub, event=event, args=[i], kwargs={})

    deadline = time.monotonic() + 5
    while fake.send_count < n:
        assert time.monotonic() < deadline, (
            f"only {fake.send_count}/{n} sends attempted"
        )
        time.sleep(0.01)

    assert remote_bus in bus._peers
    assert len(bus.subscribers(event_id)) == 1

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_dead_send_does_not_evict(create_bus: Callable[[str], Bus]):
    """The send path never evicts: peer cleanup is driven by the transport's
    disconnect notification, not by send failures."""
    bus = create_bus("tcp://127.0.0.1:15009")
    remote_bus = parse_url("tcp://127.0.0.1:15010/Proxy/0").bus

    pub = f"{bus.url.bus}/Telescope/0"
    event = "slew_begin"
    event_id = EventId(pub, event)

    bus._handle_subscribe(
        Protocol.subscribe(
            sub=f"{remote_bus}/Proxy/0", pub=pub, event=event, callback=1234
        )
    )

    fake = AlwaysDeadTransport(remote_bus)
    bus._peers[remote_bus] = _Peer(fake)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    n = 5
    for i in range(n):
        bus.publish(pub=pub, event=event, args=[i], kwargs={})

    deadline = time.monotonic() + 5
    while fake.send_count < n:
        assert time.monotonic() < deadline, (
            f"only {fake.send_count}/{n} sends attempted"
        )
        time.sleep(0.01)

    assert remote_bus in bus._peers
    assert len(bus.subscribers(event_id)) == 1

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_peer_disconnect_evicts_and_unsubscribes(create_bus: Callable[[str], Bus]):
    """When an established peer connection drops, the peer is evicted:
    outbound link gone, its subscriptions cleaned, pending requests failed."""
    bus_a = create_bus("tcp://127.0.0.1:15011")
    bus_b = create_bus("tcp://127.0.0.1:15012")

    pub = f"{bus_a.url.bus}/Telescope/0"
    event = "slew_begin"
    event_id = EventId(pub, event)

    pool = ThreadPoolExecutor()
    a_future = pool.submit(bus_a.run_forever)
    b_future = pool.submit(bus_b.run_forever)
    assert bus_a._bus_started.wait(5)
    assert bus_b._bus_started.wait(5)

    # B subscribes to an event published on A; one publish makes A actually
    # dial B so the outbound connection (and its pipe) exists
    bus_a._handle_subscribe(
        Protocol.subscribe(
            sub=f"{bus_b.url.bus}/Proxy/0", pub=pub, event=event, callback=1
        )
    )
    bus_a.publish(pub=pub, event=event, args=[], kwargs={})

    deadline = time.monotonic() + 5
    while bus_b.url.bus not in bus_a._peers:
        assert time.monotonic() < deadline, "A never connected to B"
        time.sleep(0.01)

    # a request pending on B, which will never be answered
    pending = bus_a._mailboxes.register(999_999, bus_b.url.bus)

    bus_b.shutdown()

    deadline = time.monotonic() + 5
    while bus_b.url.bus in bus_a._peers or len(bus_a.subscribers(event_id)) > 0:
        assert time.monotonic() < deadline, (
            f"peer not evicted: outbound={bus_b.url.bus in bus_a._peers}, "
            f"subscribers={len(bus_a.subscribers(event_id))}"
        )
        time.sleep(0.01)

    # the pending request was woken instead of hanging forever
    assert pending.get(timeout=5) is None

    bus_a.shutdown()
    a_future.result()
    b_future.result()
    pool.shutdown()


class BlockingTransport(AlwaysAgainTransport):
    """send blocks until released, then succeeds — a wedged peer."""

    def __init__(self, url: str, release: threading.Event):
        super().__init__(url)
        self.release = release

    def send(self, data: bytes) -> SendResult:
        self.send_count += 1
        self.release.wait(20)
        return SendResult.OK


class BlackholeTransport(AlwaysAgainTransport):
    """send accepts everything; nothing ever arrives anywhere — a silent
    partition, invisible to pipe-removal callbacks."""

    def send(self, data: bytes) -> SendResult:
        self.send_count += 1
        return SendResult.OK


def test_slow_peer_does_not_block_other_peer(create_bus: Callable[..., Bus]):
    """A sender wedged inside one peer's transport must not delay traffic to
    healthy peers: locking is per peer, not global."""
    bus = create_bus("tcp://127.0.0.1:15039")
    bus_b = create_bus("tcp://127.0.0.1:15040")

    def echo(x: int) -> int:
        return x

    bus_b.resolve_request = lambda object, method: ("/Echo/0", echo)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    b_future = pool.submit(bus_b.run_forever)
    assert bus._bus_started.wait(5)
    assert bus_b._bus_started.wait(5)

    release = threading.Event()
    slow_url = "tcp://127.0.0.1:15041"
    slow = BlockingTransport(slow_url, release)
    bus._peers[slow_url] = _Peer(slow)

    stuck = pool.submit(
        lambda: bus._push(
            Protocol.request(
                src=f"{bus.url.bus}/Proxy/0", dst=f"{slow_url}/X/0", method="x"
            )
        )
    )

    deadline = time.monotonic() + 5
    while slow.send_count < 1:
        assert time.monotonic() < deadline, "sender never entered the slow peer"
        time.sleep(0.01)

    # the healthy peer answers while the slow one holds its sender hostage
    response = bus.request(
        src=f"{bus.url.bus}/Proxy/1",
        dst=f"{bus_b.url.bus}/Echo/0",
        method="echo",
        args=[7],
        timeout=5.0,
    )
    assert response.result == 7

    release.set()
    stuck.result(timeout=5)

    bus.shutdown()
    bus_b.shutdown()
    bus_future.result()
    b_future.result()
    pool.shutdown()


def test_unresponsive_peer_evicted_by_health_check(create_bus: Callable[..., Bus]):
    """A silently partitioned peer (sends succeed, nothing ever answers) is
    evicted by the health check and its pending requests fail."""
    bus = create_bus("tcp://127.0.0.1:15042", health_timeout=0.1)

    dead_url = "tcp://127.0.0.1:15043"
    bus._peers[dead_url] = _Peer(BlackholeTransport(dead_url))

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    pending = pool.submit(
        lambda: bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst=f"{dead_url}/X/0",
            method="x",
            timeout=10.0,
        )
    )

    deadline = time.monotonic() + 5
    while not bus.stats()["mailboxes"]:
        assert time.monotonic() < deadline, "request never became pending"
        time.sleep(0.01)

    for _ in range(3):
        bus._health_check_once()

    # the pending request fails well before its own timeout
    with pytest.raises(BusDeadException):
        pending.result(timeout=5)
    assert dead_url not in bus._peers

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_evicted_peer_reconnects_on_next_send(create_bus: Callable[..., Bus]):
    """After an eviction, the next send to that bus address dials again
    transparently — a restarted peer is reachable without manual action."""
    bus_a = create_bus("tcp://127.0.0.1:15044")

    def fake_location() -> str:
        return "tcp://127.0.0.1:15045/X/0"

    bus_b = create_bus("tcp://127.0.0.1:15045")
    bus_b.resolve_request = lambda object, method: ("/X/0", fake_location)

    pool = ThreadPoolExecutor()
    a_future = pool.submit(bus_a.run_forever)
    b_future = pool.submit(bus_b.run_forever)
    assert bus_a._bus_started.wait(5)
    assert bus_b._bus_started.wait(5)

    pong = bus_a.ping(
        src=f"{bus_a.url.bus}/Proxy/0", dst="tcp://127.0.0.1:15045/X/0", timeout=5.0
    )
    assert pong is not None and pong.ok is True
    assert "tcp://127.0.0.1:15045" in bus_a._peers

    bus_b.shutdown()
    b_future.result()

    deadline = time.monotonic() + 5
    while "tcp://127.0.0.1:15045" in bus_a._peers:
        assert time.monotonic() < deadline, "dead peer never evicted"
        time.sleep(0.01)

    # a fresh bus on the same address: rebinding can take a moment
    deadline = time.monotonic() + 5
    while True:
        try:
            bus_b2 = create_bus("tcp://127.0.0.1:15045")
            break
        except Exception:
            assert time.monotonic() < deadline, "could not rebind the port"
            time.sleep(0.1)

    bus_b2.resolve_request = lambda object, method: ("/X/0", fake_location)
    b2_future = pool.submit(bus_b2.run_forever)
    assert bus_b2._bus_started.wait(5)

    pong = bus_a.ping(
        src=f"{bus_a.url.bus}/Proxy/0", dst="tcp://127.0.0.1:15045/X/0", timeout=5.0
    )
    assert pong is not None and pong.ok is True
    assert "tcp://127.0.0.1:15045" in bus_a._peers

    bus_a.shutdown()
    bus_b2.shutdown()
    a_future.result()
    b2_future.result()
    pool.shutdown()


def test_outbound_burst_not_dropped(create_bus: Callable[..., Bus]):
    """A back-to-back burst of outbound messages must survive: nng's default
    zero send buffer dropped roughly half of any burst even against a healthy
    peer (e.g. a CLI subscribing to its events at startup)."""
    bus_a = create_bus("tcp://127.0.0.1:15030")
    bus_b = create_bus("tcp://127.0.0.1:15031")

    pub = f"{bus_b.url.bus}/Telescope/0"
    event_id = EventId(pub, "tick")

    pool = ThreadPoolExecutor()
    a_future = pool.submit(bus_a.run_forever)
    b_future = pool.submit(bus_b.run_forever)
    assert bus_a._bus_started.wait(5)
    assert bus_b._bus_started.wait(5)

    # 100 subscriptions pushed as fast as the loop can go, no retries
    n = 100
    for i in range(n):
        bus_a._push(
            Protocol.subscribe(
                sub=f"{bus_a.url.bus}/Proxy/{i}", pub=pub, event="tick", callback=i
            )
        )

    deadline = time.monotonic() + 5
    while len(bus_b.subscribers(event_id)) < n:
        assert time.monotonic() < deadline, (
            f"only {len(bus_b.subscribers(event_id))}/{n} survived the burst"
        )
        time.sleep(0.01)

    bus_a.shutdown()
    bus_b.shutdown()
    a_future.result()
    b_future.result()
    pool.shutdown()


#
# pub/sub correctness: tokens, snapshots, register-before-push
#


class TickHandler:
    """Subscriber helper whose bound method is the callback."""

    def __init__(self):
        self.calls: list[str] = []
        self.received = threading.Event()

    def on_tick(self, marker: str):
        self.calls.append(marker)
        self.received.set()


def test_unsubscribe_bound_method_stops_delivery(create_bus: Callable[..., Bus]):
    """subscribe and unsubscribe get DIFFERENT bound-method objects (every
    attribute access creates one): equal by ==, different by id(). Token-based
    subscriptions must still find and remove the registration."""
    bus = create_bus("tcp://127.0.0.1:15027")
    handler = TickHandler()

    pub = f"{bus.url.bus}/Telescope/0"
    event_id = EventId(pub, "tick")

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="tick", callback=handler.on_tick
    )
    bus.publish(pub=pub, event="tick", args=["first"], kwargs={})
    assert handler.received.wait(5)

    bus.unsubscribe(
        sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="tick", callback=handler.on_tick
    )
    assert len(bus.callbacks(event_id)) == 0

    deadline = time.monotonic() + 5
    while len(bus.subscribers(event_id)) > 0:
        assert time.monotonic() < deadline, "publisher never dropped the subscriber"
        time.sleep(0.01)

    # a sentinel subscriber proves the next publish went through while the
    # unsubscribed handler stayed silent
    sentinel = threading.Event()
    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/1",
        pub=pub,
        event="tick",
        callback=lambda marker: sentinel.set(),
    )
    bus.publish(pub=pub, event="tick", args=["second"], kwargs={})
    assert sentinel.wait(5)
    time.sleep(0.1)  # settle before asserting an absence
    assert handler.calls == ["first"]

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_subscribe_registers_before_push(create_bus: Callable[..., Bus]):
    """The local callback is registered before the Subscribe message goes
    out, so a publish racing the subscription cannot fire into a gap (M6)."""
    bus = create_bus("tcp://127.0.0.1:15028")

    pub = f"{bus.url.bus}/Telescope/0"
    event_id = EventId(pub, "tick")

    seen_at_push: list[int] = []
    original_push = bus._push

    def spying_push(message):
        if isinstance(message, Subscribe):
            seen_at_push.append(len(bus.callbacks(event_id)))
        return original_push(message)

    bus._push = spying_push

    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="tick", callback=lambda: None
    )

    assert seen_at_push == [1], "callback not registered before Subscribe was pushed"

    bus._push = original_push
    bus.shutdown()


def test_pubsub_churn_no_lost_events(create_bus: Callable[..., Bus]):
    """A publish storm during subscribe/unsubscribe churn loses no events to
    the stable subscriber (unlocked iteration used to drop them silently)."""
    bus = create_bus("tcp://127.0.0.1:15029")

    pub = f"{bus.url.bus}/Telescope/0"
    n_events = 500

    count = 0
    count_lock = threading.Lock()
    done = threading.Event()

    def stable(i: int):
        nonlocal count
        with count_lock:
            count += 1
            if count == n_events:
                done.set()

    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/stable", pub=pub, event="tick", callback=stable
    )

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    stop_churn = threading.Event()

    def churn():
        i = 0
        while not stop_churn.is_set():

            def throwaway(x, _i=i):
                pass

            bus.subscribe(
                sub=f"{bus.url.bus}/Proxy/churn{i}",
                pub=pub,
                event="tick",
                callback=throwaway,
            )
            bus.unsubscribe(
                sub=f"{bus.url.bus}/Proxy/churn{i}",
                pub=pub,
                event="tick",
                callback=throwaway,
            )
            i += 1

    churn_future = pool.submit(churn)

    for i in range(n_events):
        bus.publish(pub=pub, event="tick", args=[i], kwargs={})

    assert done.wait(15), f"only {count}/{n_events} events delivered"

    stop_churn.set()
    churn_future.result(timeout=10)

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


#
# tiered dispatch: control lane vs handler pool
#


def test_hung_handlers_do_not_starve_control(create_bus: Callable[..., Bus]):
    """With every handler-pool worker wedged and more requests queued, pings
    and subscriptions must still be served: they run on their own lane."""
    bus = create_bus("tcp://127.0.0.1:15025", handler_pool_size=2)

    release = threading.Event()

    def hang() -> bool:
        release.wait(20)
        return True

    def fake_get_location() -> str:
        return "/Slow/0"

    def resolve(object: str, method: str):
        if method == "get_location":
            return "/Slow/0", fake_get_location
        return "/Slow/0", hang

    bus.resolve_request = resolve

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    # wedge both handler workers and queue two more requests behind them
    for i in range(4):
        bus._push(
            Protocol.request(
                src=f"{bus.url.bus}/Proxy/{i}",
                dst=f"{bus.url.bus}/Slow/0",
                method="hang",
            )
        )

    deadline = time.monotonic() + 5
    while bus.stats()["handler_pool"]["queued"] < 2:
        assert time.monotonic() < deadline, "handler pool never saturated"
        time.sleep(0.01)

    # liveness must survive: ping answers within its timeout...
    pong = bus.ping(
        src=f"{bus.url.bus}/Proxy/ping", dst=f"{bus.url.bus}/Slow/0", timeout=5.0
    )
    assert pong is not None and pong.ok is True

    # ...and a subscription lands (handled inline on the dispatch thread)
    pub = f"{bus.url.bus}/Telescope/0"
    event_id = EventId(pub, "slew_begin")
    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="slew_begin", callback=lambda: None
    )
    deadline = time.monotonic() + 2
    while len(bus.subscribers(event_id)) != 1:
        assert time.monotonic() < deadline, "subscribe starved by hung handlers"
        time.sleep(0.01)

    release.set()
    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_event_callback_exception_logged_not_fatal(
    create_bus: Callable[..., Bus], caplog: pytest.LogCaptureFixture
):
    """A raising event callback is logged and does not stop delivery."""
    bus = create_bus("tcp://127.0.0.1:15026")

    pub = f"{bus.url.bus}/Telescope/0"
    marker = threading.Event()

    def callback(kind: str):
        if kind == "bad":
            raise RuntimeError("callback exploded")
        marker.set()

    bus.subscribe(
        sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="tick", callback=callback
    )

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    with caplog.at_level(logging.ERROR, logger="chimera.core.bus"):
        bus.publish(pub=pub, event="tick", args=["bad"], kwargs={})
        bus.publish(pub=pub, event="tick", args=["good"], kwargs={})

        assert marker.wait(5), "later event not delivered after callback error"

        deadline = time.monotonic() + 5
        while not any("error in event handler" in r.message for r in caplog.records):
            assert time.monotonic() < deadline, "callback exception never logged"
            time.sleep(0.01)

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


#
# dispatch thread + robust shutdown
#


def test_shutdown_before_start(create_bus: Callable[[str], Bus]):
    """shutdown() on a bus that never ran must clean up, not crash."""
    bus = create_bus("tcp://127.0.0.1:15021")
    bus.shutdown()
    assert bus.is_dead()


def test_shutdown_idempotent_and_concurrent(create_bus: Callable[[str], Bus]):
    bus = create_bus("tcp://127.0.0.1:15022")

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    barrier = threading.Barrier(4)

    def shutdown():
        barrier.wait(5)
        bus.shutdown()

    futures = [pool.submit(shutdown) for _ in range(4)]
    for future in futures:
        future.result(timeout=10)

    bus_future.result(timeout=10)
    assert bus.is_dead()
    assert not bus._dispatch_thread.is_alive()

    # one more, for idempotency
    bus.shutdown()
    pool.shutdown()


def test_dispatch_crash_shuts_down_cleanly(create_bus: Callable[[str], Bus]):
    """A crash in the dispatch loop must bring the whole bus down cleanly
    instead of deadlocking on a self-join."""
    bus = create_bus("tcp://127.0.0.1:15023")

    def poisoned_pop(timeout=None):
        raise RuntimeError("poisoned")

    bus._pop = poisoned_pop

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)

    # the dispatch thread crashes immediately and the whole bus follows
    bus_future.result(timeout=5)
    assert bus.is_dead()
    pool.shutdown()


def test_shutdown_under_load(create_bus: Callable[[str], Bus]):
    """Callers in flight during shutdown get typed errors or responses,
    never hangs."""
    bus = create_bus("tcp://127.0.0.1:15024")

    def echo(x: int) -> int:
        return x

    bus.resolve_request = lambda object, method: ("/Echo/0", echo)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    stop = threading.Event()
    finished: list[int] = []
    finished_lock = threading.Lock()

    def caller(thread_id: int):
        i = 0
        while not stop.is_set():
            try:
                response = bus.request(
                    src=f"{bus.url.bus}/Proxy/{thread_id}",
                    dst=f"{bus.url.bus}/Echo/0",
                    method="echo",
                    args=[i],
                    timeout=5.0,
                )
                assert response.result == i
            except (BusDeadException, RequestTimeoutException):
                break
            i += 1
        with finished_lock:
            finished.append(thread_id)

    callers = [pool.submit(caller, thread_id) for thread_id in range(4)]

    time.sleep(0.2)  # not correctness: just lets some load build up
    bus.shutdown()
    stop.set()

    for future in callers:
        future.result(timeout=10)

    assert sorted(finished) == [0, 1, 2, 3]
    bus_future.result(timeout=10)
    pool.shutdown()


#
# request timeout + typed exceptions
#


def test_request_timeout_raises(create_bus: Callable[[str], Bus]):
    """A request whose handler never answers fails with a typed timeout
    instead of hanging the caller forever."""
    bus = create_bus("tcp://127.0.0.1:15017")

    release = threading.Event()

    def hang() -> bool:
        release.wait(10)
        return True

    bus.resolve_request = lambda object, method: ("/Slow/0", hang)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    t0 = time.monotonic()
    with pytest.raises(RequestTimeoutException):
        bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst=f"{bus.url.bus}/Slow/0",
            method="hang",
            timeout=0.3,
        )
    assert time.monotonic() - t0 < 5

    # the timed-out request left no mailbox behind
    assert len(bus._mailboxes._boxes) == 0

    release.set()
    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_request_to_never_up_peer_fails_fast(create_bus: Callable[[str], Bus]):
    """A request to a peer that never existed fails immediately with a typed
    error, not after waiting out the full timeout."""
    bus = create_bus("tcp://127.0.0.1:15018")

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    t0 = time.monotonic()
    with pytest.raises(BusDeadException):
        bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst="tcp://127.0.0.1:15019/Telescope/0",  # never bound
            method="get_az",
            timeout=10.0,  # backstop only: the refusal must fail fast
        )
    assert time.monotonic() - t0 < 2, "refused connection should fail fast"

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_request_after_shutdown_raises_bus_dead(create_bus: Callable[[str], Bus]):
    bus = create_bus("tcp://127.0.0.1:15020")

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    bus.shutdown()
    bus_future.result()

    with pytest.raises(BusDeadException):
        bus.request(
            src=f"{bus.url.bus}/Proxy/0", dst=f"{bus.url.bus}/X/0", method="get"
        )

    pool.shutdown()


#
# @lock per-object FIFO lanes
#


def test_locked_methods_serialize_per_object(create_bus: Callable[..., Bus]):
    """@lock methods of one object never run concurrently, whatever the
    handler pool does."""
    bus = create_bus("tcp://127.0.0.1:15032")

    n = 10
    concurrent = 0
    max_concurrent = 0
    calls = 0
    counter_lock = threading.Lock()

    @lock
    def locked_step() -> bool:
        nonlocal concurrent, max_concurrent, calls
        with counter_lock:
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
        time.sleep(0.01)  # widen any overlap window
        with counter_lock:
            concurrent -= 1
            calls += 1
        return True

    bus.resolve_request = lambda object, method: ("/Locked/0", locked_step)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    def call(i: int):
        return bus.request(
            src=f"{bus.url.bus}/Proxy/{i}",
            dst=f"{bus.url.bus}/Locked/0",
            method="locked_step",
            timeout=10.0,
        )

    futures = [pool.submit(call, i) for i in range(n)]
    for future in futures:
        assert future.result().code == 200

    assert calls == n
    assert max_concurrent == 1, f"locked methods overlapped: {max_concurrent}"

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_lane_fifo_order(create_bus: Callable[..., Bus]):
    """Locked methods execute in arrival order."""
    bus = create_bus("tcp://127.0.0.1:15033")

    n = 10
    order: list[int] = []
    done = threading.Event()

    @lock
    def record(i: int) -> bool:
        order.append(i)
        if len(order) == n:
            done.set()
        return True

    bus.resolve_request = lambda object, method: ("/Locked/0", record)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    # pushed from one thread: arrival order is the push order (responses have
    # no waiters and are dropped, which is fine here)
    for i in range(n):
        bus._push(
            Protocol.request(
                src=f"{bus.url.bus}/Proxy/0",
                dst=f"{bus.url.bus}/Locked/0",
                method="record",
                args=[i],
            )
        )

    assert done.wait(5)
    assert order == list(range(n))

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_hung_locked_object_does_not_block_other_object(
    create_bus: Callable[..., Bus],
):
    bus = create_bus("tcp://127.0.0.1:15034")

    release = threading.Event()

    @lock
    def hang() -> bool:
        release.wait(20)
        return True

    @lock
    def quick() -> bool:
        return True

    def resolve(object: str, method: str):
        if object == "/A/0":
            return "/A/0", hang
        return "/B/0", quick

    bus.resolve_request = resolve

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    hang_future = pool.submit(
        lambda: bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst=f"{bus.url.bus}/A/0",
            method="hang",
            timeout=30.0,
        )
    )

    deadline = time.monotonic() + 5
    while "/A/0" not in bus._lanes:
        assert time.monotonic() < deadline, "lane for A never appeared"
        time.sleep(0.01)

    # B's lane is independent: its locked method completes while A hangs
    response = bus.request(
        src=f"{bus.url.bus}/Proxy/1",
        dst=f"{bus.url.bus}/B/0",
        method="quick",
        timeout=5.0,
    )
    assert response.code == 200

    release.set()
    assert hang_future.result().code == 200

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_hung_locked_method_does_not_block_unlocked_same_object(
    create_bus: Callable[..., Bus],
):
    bus = create_bus("tcp://127.0.0.1:15035")

    release = threading.Event()

    @lock
    def hang() -> bool:
        release.wait(20)
        return True

    def get_status() -> str:
        return "ok"

    def resolve(object: str, method: str):
        if method == "hang":
            return "/A/0", hang
        return "/A/0", get_status

    bus.resolve_request = resolve

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    hang_future = pool.submit(
        lambda: bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst=f"{bus.url.bus}/A/0",
            method="hang",
            timeout=30.0,
        )
    )

    deadline = time.monotonic() + 5
    while "/A/0" not in bus._lanes:
        assert time.monotonic() < deadline, "lane never appeared"
        time.sleep(0.01)

    # unlocked methods of the same object run on the handler pool
    response = bus.request(
        src=f"{bus.url.bus}/Proxy/1",
        dst=f"{bus.url.bus}/A/0",
        method="get_status",
        timeout=5.0,
    )
    assert response.code == 200 and response.result == "ok"

    release.set()
    assert hang_future.result().code == 200

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_lane_overload_rejected_503(create_bus: Callable[..., Bus]):
    """A full lane rejects new locked requests immediately with 503, and the
    Proxy surfaces it as ObjectBusyException."""
    bus = create_bus("tcp://127.0.0.1:15036", lane_queue_size=2)

    release = threading.Event()
    entered = threading.Event()

    @lock
    def hang() -> bool:
        entered.set()
        release.wait(20)
        return True

    def fake_get_location() -> str:
        return f"{bus.url.bus}/A/0"

    def resolve(object: str, method: str):
        if method == "get_location":
            return "/A/0", fake_get_location
        return "/A/0", hang

    bus.resolve_request = resolve

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    # first the worker must be executing (queue empty), then two more fill
    # the queue — deterministic, no race with the worker's first dequeue
    bus._push(
        Protocol.request(
            src=f"{bus.url.bus}/Proxy/0", dst=f"{bus.url.bus}/A/0", method="hang"
        )
    )
    assert entered.wait(5), "locked method never started"

    for i in (1, 2):
        bus._push(
            Protocol.request(
                src=f"{bus.url.bus}/Proxy/{i}",
                dst=f"{bus.url.bus}/A/0",
                method="hang",
            )
        )

    deadline = time.monotonic() + 5
    while not any(
        lane["path"] == "/A/0" and lane["queued"] == 2 for lane in bus.stats()["lanes"]
    ):
        assert time.monotonic() < deadline, "lane never filled"
        time.sleep(0.01)

    response = bus.request(
        src=f"{bus.url.bus}/Proxy/x",
        dst=f"{bus.url.bus}/A/0",
        method="hang",
        timeout=5.0,
    )
    assert response.code == 503
    assert "busy" in response.error

    proxy = Proxy(f"{bus.url.bus}/A/0", bus)
    with pytest.raises(ObjectBusyException):
        proxy.hang()

    release.set()
    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_lane_idle_eviction_and_respawn(create_bus: Callable[..., Bus]):
    bus = create_bus("tcp://127.0.0.1:15037", lane_idle_timeout=0.2)

    @lock
    def quick() -> bool:
        return True

    bus.resolve_request = lambda object, method: ("/L/0", quick)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    src = f"{bus.url.bus}/Proxy/0"
    dst = f"{bus.url.bus}/L/0"

    assert bus.request(src=src, dst=dst, method="quick", timeout=5.0).code == 200
    assert "/L/0" in bus._lanes

    deadline = time.monotonic() + 5
    while "/L/0" in bus._lanes:
        assert time.monotonic() < deadline, "idle lane never evicted"
        time.sleep(0.02)

    # a fresh lane spawns transparently for the next locked call
    assert bus.request(src=src, dst=dst, method="quick", timeout=5.0).code == 200
    assert "/L/0" in bus._lanes

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_unlocked_methods_not_routed_to_lane(create_bus: Callable[..., Bus]):
    bus = create_bus("tcp://127.0.0.1:15038")

    def echo(x: int) -> int:
        return x

    bus.resolve_request = lambda object, method: ("/Echo/0", echo)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    for i in range(5):
        response = bus.request(
            src=f"{bus.url.bus}/Proxy/0",
            dst=f"{bus.url.bus}/Echo/0",
            method="echo",
            args=[i],
            timeout=5.0,
        )
        assert response.result == i

    assert bus._lanes == {}

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


#
# soak: everything at once, sustained
#


@pytest.mark.slow
def test_soak_no_crossed_responses_no_lost_events(create_bus: Callable[..., Bus]):
    """a ~100 Hz publisher plus 8 concurrent RPC threads across two real buses.
    Zero crossed responses, zero lost subscriptions, >=99% event delivery, no
    leaked mailboxes and bounded memory growth.
    Set CHIMERA_SOAK_SECONDS=60 for the full soak."""
    import subprocess

    duration = float(os.environ.get("CHIMERA_SOAK_SECONDS", "5"))

    server = create_bus("tcp://127.0.0.1:15046")
    client = create_bus("tcp://127.0.0.1:15047")

    def echo(x: int) -> int:
        return x

    server.resolve_request = lambda object, method: ("/Echo/0", echo)

    pool = ThreadPoolExecutor(max_workers=16)
    server_future = pool.submit(server.run_forever)
    client_future = pool.submit(client.run_forever)
    assert server._bus_started.wait(5)
    assert client._bus_started.wait(5)

    pub = f"{server.url.bus}/Telescope/0"
    event_id = EventId(pub, "tick")

    events_received = 0
    events_lock = threading.Lock()

    def on_tick(i: int) -> None:
        nonlocal events_received
        with events_lock:
            events_received += 1

    client.subscribe(
        sub=f"{client.url.bus}/Proxy/sub", pub=pub, event="tick", callback=on_tick
    )
    deadline = time.monotonic() + 5
    while len(server.subscribers(event_id)) != 1:
        assert time.monotonic() < deadline, "subscription never propagated"
        time.sleep(0.01)

    def rss_kb() -> int:
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(os.getpid())])
        return int(out.strip())

    rss_start = rss_kb()
    stop = threading.Event()
    crossed = 0
    rpc_ok = 0
    rpc_errors = 0
    counters_lock = threading.Lock()

    def rpc_worker(thread_id: int) -> None:
        nonlocal crossed, rpc_ok, rpc_errors
        i = 0
        while not stop.is_set():
            value = thread_id * 10_000_000 + i
            try:
                response = client.request(
                    src=f"{client.url.bus}/Proxy/{thread_id}",
                    dst=f"{server.url.bus}/Echo/0",
                    method="echo",
                    args=[value],
                    timeout=10.0,
                )
                with counters_lock:
                    if response.result != value:
                        crossed += 1
                    else:
                        rpc_ok += 1
            except (BusDeadException, RequestTimeoutException):
                with counters_lock:
                    rpc_errors += 1
            i += 1

    events_published = 0

    def publisher() -> None:
        nonlocal events_published
        while not stop.is_set():
            server.publish(pub=pub, event="tick", args=[events_published], kwargs={})
            events_published += 1
            time.sleep(0.01)  # ~100 Hz

    workers = [pool.submit(rpc_worker, thread_id) for thread_id in range(8)]
    publisher_future = pool.submit(publisher)

    time.sleep(duration)
    stop.set()
    for worker in workers:
        worker.result(timeout=30)
    publisher_future.result(timeout=30)

    time.sleep(1.0)  # drain in-flight events
    rss_end = rss_kb()

    assert rpc_ok > 0
    assert crossed == 0, f"{crossed} crossed responses"
    assert rpc_errors == 0, f"{rpc_errors} rpc errors"
    assert len(server.subscribers(event_id)) == 1, "subscription lost"
    assert events_received >= events_published * 0.99, (
        f"event loss: {events_received}/{events_published}"
    )
    assert len(client.stats()["mailboxes"]) == 0
    assert len(server.stats()["mailboxes"]) == 0
    assert rss_end < rss_start + 100_000, (
        f"rss grew {rss_end - rss_start} kB during the soak"
    )

    client.shutdown()
    server.shutdown()
    client_future.result(timeout=10)
    server_future.result(timeout=10)
    pool.shutdown()


#
# observability (chimera-ctl status)
#


class StatusInstrument(ChimeraObject):
    __config__ = {"speed": 42.0}

    def get_speed(self) -> float:
        return self["speed"]


class LoopingInstrument(StatusInstrument):
    def control(self) -> bool:
        return True


def test_bus_stats_snapshot(create_bus: Callable[[str], Bus]):
    """Bus.stats() reports liveness, pending mailboxes with ages, peers and
    pub/sub tables — and the whole snapshot survives the wire format."""
    bus = create_bus("tcp://127.0.0.1:15013")

    release = threading.Event()

    def slow() -> bool:
        release.wait(10)
        return True

    bus.resolve_request = lambda object, method: ("/Slow/0", slow)

    pub = f"{bus.url.bus}/Telescope/0"
    bus._handle_subscribe(
        Protocol.subscribe(
            sub=f"{bus.url.bus}/Proxy/0", pub=pub, event="slew_begin", callback=7
        )
    )

    peer_url = "tcp://127.0.0.1:15016"
    bus._peers[peer_url] = _Peer(AlwaysAgainTransport(peer_url))

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    request_future = pool.submit(
        lambda: bus.request(
            src=f"{bus.url.bus}/Proxy/0", dst=f"{bus.url.bus}/Slow/0", method="slow"
        )
    )

    deadline = time.monotonic() + 5
    while not bus.stats()["mailboxes"]:
        assert time.monotonic() < deadline, "pending request never showed up"
        time.sleep(0.01)

    stats = bus.stats()
    assert stats["url"] == bus.url.url
    assert stats["inbox_url"] == bus.url.bus
    assert stats["running"] is True and stats["started"] is True
    box = stats["mailboxes"][0]
    assert box["dst_bus"] == bus.url.bus
    assert box["age"] >= 0
    assert peer_url in stats["peers"]
    assert {"publisher": pub, "event": "slew_begin", "subscribers": 1} in stats[
        "subscribers"
    ]

    # pool snapshot: limits, backlog and per-thread state (the pool spawns
    # lazily, so wait until the pending request's handler occupies a thread)
    deadline = time.monotonic() + 5
    while not bus.stats()["handler_pool"]["threads"]:
        assert time.monotonic() < deadline, "handler never occupied a pool thread"
        time.sleep(0.01)

    pool_info = bus.stats()["handler_pool"]
    assert pool_info["max_workers"] >= 1
    assert pool_info["queued"] >= 0
    for thread in pool_info["threads"]:
        assert thread["id"] and thread["name"]
        assert thread["alive"] is True

    # the whole snapshot must survive the wire format
    msgspec.json.encode(stats)

    release.set()
    assert request_future.result().code == 200

    bus.shutdown()
    bus_future.result()
    assert bus.stats()["running"] is False
    pool.shutdown()


def test_manager_status_over_proxy(create_bus: Callable[[str], Bus]):
    """The chimera-ctl path: resolve the Manager through a Proxy (requires
    Manager.get_location) and fetch the full system status over the bus."""
    bus = create_bus("tcp://127.0.0.1:15014")
    manager = Manager(bus)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    manager.add_class(StatusInstrument, "fake", start=False)
    manager.add_class(LoopingInstrument, "looper", start=True)

    proxy = Proxy(f"{bus.url.bus}/Manager/0", bus)
    proxy.resolve()  # pings; fails without Manager.get_location

    status = proxy.get_status()

    assert status["system"]["pid"] == os.getpid()
    assert status["bus"]["url"] == bus.url.url
    assert status["bus"]["running"] is True

    objects = {obj["path"]: obj for obj in status["objects"]}
    assert "/Manager/manager" in objects

    fake = objects["/StatusInstrument/fake"]
    assert fake["class"] == "StatusInstrument"
    assert fake["state"] == "STOPPED"
    assert fake["loop"] == "none"
    assert fake["loop_id"] is None
    assert fake["config"]["speed"] == 42.0
    assert fake["age"] >= 0

    # the running control loop reports the OS thread it runs on, and that
    # thread shows up in the control-loops pool
    deadline = time.monotonic() + 5
    looper = None
    while time.monotonic() < deadline:
        looper = {obj["path"]: obj for obj in manager.get_status()["objects"]}[
            "/LoopingInstrument/looper"
        ]
        if looper["loop_id"] is not None:
            break
        time.sleep(0.01)

    assert looper is not None and looper["loop"] == "running"
    assert looper["state"] == "RUNNING"
    assert isinstance(looper["loop_id"], int)

    manager_pool = manager.get_status()["pool"]
    assert manager_pool["max_workers"] >= 1
    assert looper["loop_id"] in [thread["id"] for thread in manager_pool["threads"]]

    manager.shutdown()
    bus.shutdown()
    bus_future.result()
    pool.shutdown()


#
# response correlation by request id (reply mailboxes)
#


def test_concurrent_requests_one_src_are_correlated(create_bus: Callable[[str], Bus]):
    """Concurrent requests sharing one src URL must each get their own
    response, matched by request id — never a sibling's reply."""
    bus = create_bus("tcp://127.0.0.1:15007")

    def echo(x: int) -> int:
        return x

    bus.resolve_request = lambda object, method: ("/Echo/0", echo)

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    src = f"{bus.url.bus}/Proxy/shared"
    dst = f"{bus.url.bus}/Echo/0"
    n_threads, n_requests = 4, 200
    errors: list[str] = []

    def caller(thread_id: int):
        for i in range(n_requests):
            value = thread_id * 1_000_000 + i
            response = bus.request(src=src, dst=dst, method="echo", args=[value])
            if response is None or response.result != value:
                errors.append(
                    f"thread {thread_id} sent {value}, "
                    f"got {response.result if response else None}"
                )
                return

    futures = [pool.submit(caller, thread_id) for thread_id in range(n_threads)]
    for future in futures:
        future.result()

    assert not errors, errors[:5]

    # every mailbox was unregistered once its request completed
    assert len(bus._mailboxes._boxes) == 0

    bus.shutdown()
    bus_future.result()
    pool.shutdown()


def test_unmatched_response_dropped(
    create_bus: Callable[[str], Bus], caplog: pytest.LogCaptureFixture
):
    """A Response whose id has no registered waiter (late reply after a
    timeout, stray id) is dropped and logged, not queued forever."""
    bus = create_bus("tcp://127.0.0.1:15008")

    pool = ThreadPoolExecutor()
    bus_future = pool.submit(bus.run_forever)
    assert bus._bus_started.wait(5)

    request = Protocol.request(
        src=f"{bus.url.bus}/Proxy/0",
        dst=f"{bus.url.bus}/Echo/0",
        method="echo",
        args=[1],
    )
    orphan = request.ok(42.0)

    with caplog.at_level(logging.DEBUG, logger="chimera.core.bus"):
        # local delivery is synchronous: no waiter registered for this id
        bus._push(orphan)

    assert any("no waiter" in record.message for record in caplog.records)
    assert len(bus._mailboxes._boxes) == 0

    bus.shutdown()
    bus_future.result()
    pool.shutdown()
