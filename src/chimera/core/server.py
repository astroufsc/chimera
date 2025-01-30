import operator
import logging
from concurrent.futures import ThreadPoolExecutor

from chimera.core.resources import ResourcesManager
from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.protocol import Protocol
from chimera.core.transport import create_transport
from chimera.core.transport_redis import RedisTransport


log = logging.getLogger(__name__)


class Server:
    def __init__(
        self,
        resources: ResourcesManager,
        host,
        port,
        protocol=Protocol,
        transport=RedisTransport,
        serializer=PickleSerializer,
        pool=ThreadPoolExecutor,
    ):
        self.resources = resources
        self.transport = create_transport(host, port, transport, serializer)
        self.pool = pool()
        self.protocol = protocol()

    def start(self):
        self.transport.bind()

    def stop(self):
        try:
            self.transport.close()
        except ConnectionRefusedError:
            # server might be down already, just ignore
            log.warning("Server is down already, exiting.")

    def ping(self):
        return self.transport.ping()

    def loop(self):
        while True:
            request = self.transport.recv_request()
            if request is None:
                # server is down, return to avoid infinite loop
                return

            self.pool.submit(self._handle_request, request)

    def _handle_request(self, request):
        resource = self.resources.get(request.location)
        if not resource:
            self.transport.send_response(
                request,
                self.protocol.not_found(f"Resource {request.location} not found"),
            )

        instance = resource.instance
        method_getter = operator.attrgetter(request.method)

        try:
            method = method_getter(instance)
        except AttributeError:
            return self.transport.send_response(
                request, self.protocol.not_found(f"Method {request.method} not found")
            )

        try:
            result = method(*request.args, **request.kwargs)
            self.transport.send_response(request, self.protocol.ok(result))
        except Exception as e:
            self.transport.send_response(request, self.protocol.error(e))

    def publish(self, topic, *args, **kwargs):
        self.transport.publish(topic, self.protocol.event(*args, **kwargs))
