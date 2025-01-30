import logging
from typing import Type

import redis
import redislite
from chimera.core.protocol import Event, Request, Response
from chimera.core.serializer import Serializer
from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.transport import Transport


log = logging.getLogger(__name__)


class RedisTransport(Transport):
    REQUESTS_KEY: str = "chimera_requests"

    DEFAULT_TIMEOUT: int = 5 * 60  # 5 minutes
    LOOP_TICK: int = 1

    def __init__(
        self, host: str, port: int, serializer: Type[Serializer] = PickleSerializer
    ):
        super().__init__(host, port, serializer)
        self._r = None
        self._pubsub = None
        self._pubsub_thread = None

    def bind(self):
        self._r = redislite.Redis(serverconfig={"bind": self.host, "port": self.port})
        self._r.delete(RedisTransport.REQUESTS_KEY)
        self._init_pubsub()

    def _init_pubsub(self):
        if self._pubsub is None:  # avoid creating multiple pubsub instances
            self._pubsub = self._r.pubsub()
            self._pubsub_thread = self._pubsub.run_in_thread(
                daemon=True, sleep_time=0.001
            )

    def connect(self):
        if self._r is None:
            self._r = redislite.Redis(host=self.host, port=self.port)
            self._init_pubsub()

    def _close_pubsub(self):
        if self._pubsub is not None:
            self._pubsub.close()
            self._pubsub_thread.stop()

    def close(self):
        # close pubsub
        self._close_pubsub()
        # shutdown the server
        self._r.shutdown()

    def ping(self) -> bool:
        try:
            return self._r.ping()
        except redis.exceptions.ConnectionError:
            log.error("ping failed. Is server down?")
            return False

    def send_request(self, request: Request) -> None:
        request_bytes = self.serializer.dumps(request)

        try:
            self._r.rpush(self.REQUESTS_KEY, request_bytes)
        except redis.exceptions.ConnectionError:
            # server is down, just ignore
            return

    def recv_request(self) -> Request | None:
        try:
            data = self._r.blpop(
                [
                    self.REQUESTS_KEY,
                ]
            )
            _, request_bytes = data
            return self.serializer.loads(request_bytes)
        except redis.exceptions.ConnectionError:
            return None

    def send_response(self, request: Request, response: Response) -> None:
        response_bytes = self.serializer.dumps(response)
        self._r.rpush(f"chimera_response_{request.id}", response_bytes)

    def recv_response(self, request: Request) -> Response | None:
        try:
            data = self._r.blpop(
                [
                    f"chimera_response_{request.id}",
                ]
            )
            _, request_bytes = data
            return self.serializer.loads(request_bytes)
        except redis.exceptions.ConnectionError:
            return None

    def publish(self, topic: str, data: Event) -> int:
        """Publish a message to a topic. Return the number of subscribers."""
        return self._r.publish(topic, self.serializer.dumps(data))

    def subscribe(self, topic: str, callback) -> None:
        def parse_call(message):
            event = self.serializer.loads(message["data"])
            try:
                callback(*event.args, **event.kwargs)
            except:
                log.exception("Error while calling callback")
                raise

        self._pubsub.subscribe(**{topic: parse_call})

    def unsubscribe(self, channel: str, callback) -> None:
        self._pubsub.unsubscribe(channel)
