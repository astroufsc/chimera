import logging
from typing import Type, override

import redis
import redis.exceptions
import redislite

from chimera.core.protocol import Event, Request, Response
from chimera.core.serializer import Serializer
from chimera.core.transport import Transport

log = logging.getLogger(__name__)


class RedisTransport(Transport):
    REQUESTS_KEY: str = "chimera_requests"

    def __init__(self, host: str, port: int, serializer: Type[Serializer]):
        super().__init__(host, port, serializer)
        self._r: redis.Redis | None = None
        self._pubsub = None
        self._pubsub_thread = None

    @override
    def bind(self) -> None:
        self._r = redislite.Redis(serverconfig={"bind": self.host, "port": self.port})
        self._r.delete(RedisTransport.REQUESTS_KEY)
        self._init_pubsub()

    def _init_pubsub(self):
        assert self._r is not None

        def exception_handler(e, pubsub, thread):
            if isinstance(e, redis.ConnectionError):
                # connection died, just ignore as this is probably due to server shutdown
                return
            raise e

        if self._pubsub is None:
            self._pubsub = self._r.pubsub()
            self._pubsub_thread = self._pubsub.run_in_thread(
                daemon=True, sleep_time=0.001, exception_handler=exception_handler
            )
            self._pubsub_thread.name = f"{self.host}:{self.port}/RedisTransport/0"

    @override
    def connect(self) -> None:
        if self._r is None:
            self._r = redislite.Redis(host=self.host, port=self.port)
            self._init_pubsub()

    def _close_pubsub(self):
        if self._pubsub is not None:
            self._pubsub.close()
            self._pubsub_thread.stop()

    @override
    def close(self) -> None:
        assert self._r is not None
        self._close_pubsub()
        self._r.shutdown()

    @override
    def ping(self) -> bool:
        assert self._r is not None
        try:
            return self._r.ping()
        except redis.exceptions.ConnectionError:
            log.error("ping failed. Is server down?")
            return False

    @override
    def send_request(self, request: Request) -> None:
        assert self._r is not None
        request_bytes = request.dump(self.serializer)
        if not request_bytes:
            # TODO: is this the better way to handle this?
            log.error("Failed to serialize request")
            return

        try:
            self._r.rpush(self.REQUESTS_KEY, request_bytes)
        except redis.exceptions.ConnectionError:
            # server is down, just ignore
            return

    @override
    def recv_request(self) -> Request | None:
        assert self._r is not None
        try:
            data = self._r.blpop(
                [
                    self.REQUESTS_KEY,
                ]
            )
            _, request_bytes = data
            return Request.load(self.serializer, request_bytes)
        except redis.exceptions.ConnectionError:
            return None

    @override
    def send_response(self, request: Request, response: Response) -> None:
        assert self._r is not None
        response_bytes = response.dump(self.serializer)
        if response_bytes is None:
            # TODO: is this the better way to handle this?
            log.error("Failed to serialize response")
            return
        self._r.rpush(f"chimera_response_{request.id}", response_bytes)

    @override
    def recv_response(self, request: Request) -> Response | None:
        assert self._r is not None
        try:
            data = self._r.blpop(
                [
                    f"chimera_response_{request.id}",
                ]
            )
            _, request_bytes = data
            return Response.load(self.serializer, request_bytes)
        except redis.exceptions.ConnectionError:
            return None

    @override
    def publish(self, topic: str, event: Event) -> None:
        assert self._r is not None
        """Publish a message to a topic. Return the number of subscribers."""
        self._r.publish(topic, event.dump(self.serializer))

    @override
    def subscribe(self, topic: str, callback) -> None:
        assert self._pubsub is not None

        def parse_call(message):
            event = self.serializer.loads(message["data"])
            try:
                callback(*event.args, **event.kwargs)
            except:
                log.exception("Error while calling callback")
                raise

        self._pubsub.subscribe(**{topic: parse_call})

    @override
    def unsubscribe(self, topic: str, callback) -> None:
        assert self._pubsub is not None
        self._pubsub.unsubscribe(topic)
