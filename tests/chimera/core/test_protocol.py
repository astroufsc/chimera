import time
from typing import Any
from unittest.mock import Mock, patch

from chimera.core.protocol import (
    Event,
    Ping,
    Pong,
    Protocol,
    Publish,
    Request,
    Response,
    Subscribe,
    Unsubscribe,
)


class TestProtocol:
    def setup_method(self):
        self.src = "host1:1234/Telescope/instance1"
        self.dst = "host2:5678/Camera/instance2"

    def test_id_generation(self):
        """Test ID generation produces integer values"""
        id1 = Protocol.id()
        id2 = Protocol.id()

        assert isinstance(id1, int)
        assert isinstance(id2, int)
        assert 0 <= id1 <= 2**32
        # IDs should be different (possible but extremely unlikely they would be the same)
        assert id1 != id2

    def test_timestamp_generation(self):
        """Test timestamp generation produces increasing values"""
        ts1 = Protocol.timestamp()
        time.sleep(0.001)  # Small delay to ensure timestamp changes
        ts2 = Protocol.timestamp()

        assert isinstance(ts1, int)
        assert ts2 > ts1  # Timestamps should increase

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_ping_creation(self, mock_timestamp: Mock):
        """Test ping message creation"""
        mock_timestamp.return_value = 12345

        ping = Protocol.ping(src=self.src, dst=self.dst)

        assert isinstance(ping, Ping)
        assert ping.ts == 12345
        assert ping.src == self.src
        assert ping.dst == self.dst

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_pong_creation(self, mock_timestamp: Mock):
        """Test pong message creation"""
        mock_timestamp.return_value = 12345

        ping = Protocol.ping(src=self.src, dst=self.dst)

        pong = ping.pong()

        assert isinstance(pong, Pong)
        assert pong.ts == 12345
        assert pong.src == self.dst
        assert pong.dst == self.src
        assert pong.ok is True

    @patch("chimera.core.protocol.Protocol.timestamp")
    @patch("chimera.core.protocol.Protocol.id")
    def test_request_creation(self, mock_id: Mock, mock_timestamp: Mock):
        """Test request message creation"""
        mock_timestamp.return_value = 12345
        mock_id.return_value = 42

        method = "get_position"
        args = [10, 20]
        kwargs = {"precision": "high"}

        request = Protocol.request(
            src=self.src, dst=self.dst, method=method, args=args, kwargs=kwargs
        )

        assert isinstance(request, Request)
        assert request.id == 42
        assert request.ts == 12345
        assert request.src == self.src
        assert request.dst == self.dst
        assert request.method == method
        assert request.args == args
        assert request.kwargs == kwargs

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_request_ok_response(self, mock_timestamp: Mock):
        """Test creating an OK response from a request"""
        mock_timestamp.return_value = 67890

        request = Request(
            id=42,
            ts=12345,
            src=self.src,
            dst=self.dst,
            method="get_position",
            args=[],
            kwargs={},
        )

        result = {"ra": 10.5, "dec": -30.2}
        response = request.ok(result)

        assert isinstance(response, Response)
        assert response.id == request.id
        assert response.ts == 67890
        assert response.src == request.dst  # Response source is request destination
        assert response.dst == request.src  # Response destination is request source
        assert response.code == 200
        assert response.result == result
        assert response.error is None

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_request_error_response(self, mock_timestamp: Mock):
        """Test creating an error response from a request"""
        mock_timestamp.return_value = 67890

        request = Request(
            id=42,
            ts=12345,
            src=self.src,
            dst=self.dst,
            method="get_position",
            args=[],
            kwargs={},
        )

        # Create an exception to use in the error response
        error = ValueError("Position not available")
        response = request.error(error)

        assert isinstance(response, Response)
        assert response.id == request.id
        assert response.ts == 67890
        assert response.src == request.dst
        assert response.dst == request.src
        assert response.code == 500
        assert response.result is None
        assert response.error is not None
        assert "ValueError: Position not available" in response.error
        assert "traceback=" in response.error  # Check traceback is included

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_request_not_found_response(self, mock_timestamp: Mock):
        """Test creating a not found response from a request"""
        mock_timestamp.return_value = 67890

        request = Request(
            id=42,
            ts=12345,
            src=self.src,
            dst=self.dst,
            method="get_nonexistent_method",
            args=[],
            kwargs={},
        )

        # Now we can call the method
        response = request.not_found("get_nonexistent_method does not exists")

        assert isinstance(response, Response)
        assert response.id == request.id
        assert response.ts == 67890
        assert response.src == request.dst
        assert response.dst == request.src
        assert response.code == 404
        assert response.result is None
        assert response.error == "get_nonexistent_method does not exists"

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_subscribe_creation(self, mock_timestamp: Mock):
        """Test subscribe message creation"""
        mock_timestamp.return_value = 12345

        def on_slew_complete(): ...

        event = "slew_complete"
        callback = id(on_slew_complete)

        subscribe = Protocol.subscribe(
            sub=self.dst, pub=self.src, event=event, callback=callback
        )

        assert isinstance(subscribe, Subscribe)
        assert subscribe.ts == 12345
        assert subscribe.pub == self.src
        assert subscribe.sub == self.dst
        assert subscribe.event == event
        assert subscribe.callback == callback

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_unsubscribe_creation(self, mock_timestamp: Mock):
        """Test unsubscribe message creation"""
        mock_timestamp.return_value = 12345

        def on_slew_complete(): ...

        event = "slew_complete"
        callback = id(on_slew_complete)

        unsubscribe = Protocol.unsubscribe(
            sub=self.dst, pub=self.src, event=event, callback=callback
        )

        assert isinstance(unsubscribe, Unsubscribe)
        assert unsubscribe.ts == 12345
        assert unsubscribe.pub == self.src
        assert unsubscribe.sub == self.dst
        assert unsubscribe.event == event
        assert unsubscribe.callback == callback

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_publish_creation(self, mock_timestamp: Mock):
        """Test publish message creation"""
        mock_timestamp.return_value = 12345

        event = "image_ready"
        args = ["image1.fits"]
        kwargs = {"size": 1024}

        publish = Protocol.publish(pub=self.src, event=event, args=args, kwargs=kwargs)

        assert isinstance(publish, Publish)
        assert publish.ts == 12345
        assert publish.pub == self.src
        assert publish.event == event
        assert publish.args == args
        assert publish.kwargs == kwargs

    @patch("chimera.core.protocol.Protocol.timestamp")
    def test_publish_to_event(self, mock_timestamp: Mock):
        """Test converting a publish message to an event message"""
        mock_timestamp.return_value = 67890

        publish = Publish(
            ts=12345,
            pub=self.src,
            event="image_ready",
            args=["image1.fits"],
            kwargs={"size": 1024},
        )

        subscriber_url = "host3:9012/Observer/instance3"
        event_name = "on_image_ready"
        event_args = ["image1.fits"]
        event_kwargs: dict[str, Any] = {"size": 1024, "processed": True}

        event = publish.callback(
            dst=subscriber_url, event=event_name, args=event_args, kwargs=event_kwargs
        )

        assert isinstance(event, Event)
        assert event.ts == 67890
        assert event.src == publish.pub
        assert event.dst == subscriber_url
        assert event.event == event_name
        assert event.args == event_args
        assert event.kwargs == event_kwargs

    @patch("chimera.core.protocol.Protocol.timestamp")
    @patch("chimera.core.protocol.Protocol.id")
    def test_error_creation(self, mock_id: Mock, mock_timestamp: Mock):
        """Test creating error response directly from Protocol"""
        mock_timestamp.return_value = 67890
        mock_id.return_value = 42

        error = RuntimeError("Something went wrong")
        response = Protocol.error(src=self.src, dst=self.dst, error=error)

        assert isinstance(response, Response)
        assert response.id == 42
        assert response.ts == 67890
        assert response.src == self.src
        assert response.dst == self.dst
        assert response.code == 500
        assert response.result is None
        assert response.error is not None
        assert "RuntimeError: Something went wrong" in response.error
        assert "traceback=" in response.error

    def test_end_to_end_request_response_flow(self):
        """Test a complete request-response flow"""

        # Create a request
        request = Protocol.request(
            src=self.src,
            dst=self.dst,
            method="get_coordinates",
            args=[],
            kwargs={"format": "degrees"},
        )

        # Simulate processing and create a response
        result = {"ra": 15.5, "dec": 30.2}
        response = request.ok(result)

        # Verify the flow
        assert response.id == request.id
        assert response.src == request.dst
        assert response.dst == request.src
        assert response.code == 200
        assert response.result == result

    def test_end_to_end_publish_event_flow(self):
        """Test a complete publish-event flow"""
        # Create a publish message
        event_name = "observation_complete"
        publish = Protocol.publish(
            pub=self.src,
            event=event_name,
            args=["NGC1234"],
            kwargs={"duration": 3600},
        )

        # Create events for subscribers
        subscriber1 = "host:port/Logger/instance1"
        subscriber2 = "host:port/DataProcessor/instance2"

        event1 = publish.callback(
            dst=subscriber1,
            event=event_name,
            args=publish.args,
            kwargs=publish.kwargs,
        )

        event2 = publish.callback(
            dst=subscriber2,
            event=event_name,
            args=publish.args,
            kwargs=publish.kwargs,
        )

        # Verify the flow
        assert event1.src == publish.pub
        assert event1.dst == subscriber1
        assert event1.event == event_name
        assert event1.args == publish.args
        assert event1.kwargs == publish.kwargs

        assert event2.src == publish.pub
        assert event2.dst == subscriber2
        assert event2.event == event_name
        assert event2.args == publish.args
        assert event2.kwargs == publish.kwargs

    def test_subscription_workflow(self):
        """Test the complete subscription workflow"""

        def on_filter_changed():
            pass

        event_name = "filter_changed"
        callback = id(on_filter_changed)

        # Create subscribe message
        subscribe = Protocol.subscribe(
            sub=self.dst, pub=self.src, event=event_name, callback=callback
        )

        # Verify subscribe message
        assert subscribe.event == event_name
        assert subscribe.callback == callback

        # Create unsubscribe message
        unsubscribe = Protocol.unsubscribe(
            sub=self.dst, pub=self.src, event=event_name, callback=callback
        )

        # Verify unsubscribe message
        assert unsubscribe.event == event_name
        assert unsubscribe.callback == callback

        # The subscribe and unsubscribe should reference the same event and callback
        assert subscribe.event == unsubscribe.event
        assert subscribe.callback == unsubscribe.callback
