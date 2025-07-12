import time
from collections.abc import Callable
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any, Literal
from unittest.mock import MagicMock

from chimera.core.bus import Bus, Callback, CallbackId, EventId, Subscriber
from chimera.core.url import parse_url


def print_results(op: str, n: int, dt: float):
    ops = f"{op}/s"
    print(
        f"{op:20}[{n}] {dt:.6f}s {n / dt:.0f} {ops:<20} {(dt * 1_000_000 / n):.3f} μs/{op}"
    )


def ping_test(*, n: int, src_bus: Bus, dst_bus: Bus):
    print()

    src = f"{src_bus.url.url}/Proxy/932032"
    dst = f"{dst_bus.url.url}/Telescope/0"

    def sender():
        t0 = time.monotonic()
        for _ in range(n):
            pong = src_bus.ping(src=src, dst=dst)
            assert pong is not None and pong.ok is True
        print_results("ping", n, time.monotonic() - t0)

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

    dst = f"{dst_bus.url.url}/Telescope/0"
    src = f"{src_bus.url.url}/Proxy/0"

    src_not_found = f"{src_bus.url.url}/Proxy/1"
    dst_not_found = f"{dst_bus.url.url}/Telescope/not-found"

    def fake_get_az():
        return 42.0

    def resolve_request(
        object: str, method: str
    ) -> tuple[bool, Literal[False] | Callable[..., Any]]:
        if object == "/Telescope/0" and method == "get_az":
            return True, fake_get_az
        elif object == "/Telescope/0" and method == "unknown_method":
            return True, False
        return False, False

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

    sub = [f"{src_bus.url.url}/Proxy/{i}" for i in range(n_subscribers)]
    pub = f"{dst_bus.url.url}/Telescope/0"

    def create_callback(i: int):
        def on_slew_begin(ra: float, dec: float, slew_status: str):
            assert ra == 42.0 + i
            assert dec == 50.0 + i
            assert slew_status == "complete"

        return MagicMock(on_slew_begin)

    callbacks = [create_callback(i) for i in range(n_subscribers)]
    assert (
        len(set([id(cb) for cb in callbacks])) == n_subscribers
    ), "callbacks must be unique"

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


def test_ping_local():
    bus = Bus("tcp://127.0.0.1:2000")
    ping_test(n=50_000, src_bus=bus, dst_bus=bus)


def test_ping_remote():
    my_bus = Bus("tcp://127.0.0.1:2001")
    other_bus = Bus("tcp://127.0.0.1:2002")
    ping_test(n=10_000, src_bus=my_bus, dst_bus=other_bus)


def test_rpc_local():
    bus = Bus("tcp://127.0.0.1:3000")
    rpc_test(n=10_000, src_bus=bus, dst_bus=bus)


def test_rpc_remote():
    my_bus = Bus("tcp://127.0.0.1:3001")
    other_bus = Bus("tcp://127.0.0.1:3002")
    rpc_test(n=2_000, src_bus=my_bus, dst_bus=other_bus)


def test_pubsub_local():
    bus = Bus("tcp://127.0.0.1:4000")
    pubsub_test(n_subscribers=2, n_events=1_000, src_bus=bus, dst_bus=bus)


def test_pubsub_remote():
    my_bus = Bus("tcp://127.0.0.1:4001")
    other_bus = Bus("tcp://127.0.0.1:4002")
    pubsub_test(n_subscribers=2, n_events=1_000, src_bus=my_bus, dst_bus=other_bus)
