import logging
import time
from typing import Type

import redis
import redislite
from chimera.core.protocol import Request, Response
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
        self.r = None
        self.pubsub = None
        self.pubsub_threads = []

    def bind(self):
        self.r = redislite.Redis(serverconfig={"bind": self.host, "port": self.port})
        self.r.delete(RedisTransport.REQUESTS_KEY)
        self._init_pubsub()

    def _init_pubsub(self):
        self.pubsub = self.r.pubsub()

    def connect(self):
        self.r = redislite.Redis(host=self.host, port=self.port)

    def _close_pubsub(self):
        # close pubsub threads bofore closing the connection
        if len(self.pubsub_threads) > 0:
            for thread in self.pubsub_threads:
                thread.stop()
            time.sleep(0.1)
            self.pubsub.close()

    def close(self):
        # close pubsub thread
        self._close_pubsub()
        # shutdown the server
        self.r.shutdown()

    def ping(self) -> bool:
        try:
            return self.r.ping()
        except redis.exceptions.ConnectionError:
            log.error("ping failed. Is server down?")
            return False

    def send_request(self, request: Request) -> None:
        request_bytes = self.serializer.dumps(request)

        try:
            self.r.rpush(self.REQUESTS_KEY, request_bytes)
        except redis.exceptions.ConnectionError:
            # server is down, just ignore
            return

    def recv_request(self) -> Request | None:
        try:
            data = self.r.blpop(
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
        self.r.rpush(f"chimera_response_{request.id}", response_bytes)

    def recv_response(self, request: Request) -> Response | None:
        try:
            data = self.r.blpop(
                [
                    f"chimera_response_{request.id}",
                ]
            )
            _, request_bytes = data
            return self.serializer.loads(request_bytes)
        except redis.exceptions.ConnectionError:
            return None

    def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel. Return the number of subscribers."""
        return self.r.publish(channel, self.serializer.dumps(message))

    def subscribe(self, channel: str, callback) -> None:
        def clbk(message):
            callback(self.serializer.loads(message["data"]))
            callback(self.serializer.loads(message["data"]))

        self.pubsub.subscribe(**{channel: clbk})
        self.pubsub_threads.append(self.pubsub.run_in_thread(daemon=True))
