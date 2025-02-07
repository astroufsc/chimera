import operator
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

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
        self.pool = pool(thread_name_prefix=f"{host}:{port}/Server")
        self.protocol = protocol()
        self._running = threading.Event()

    def start(self):
        self.transport.bind()

    def stop(self):
        try:
            self._running.clear()
            self.pool.shutdown()
            self.transport.close()
        except ConnectionRefusedError:
            # server might be down already, just ignore
            log.warning("Server is down already, exiting.")

    def ping(self):
        return self.transport.ping()

    def loop(self):
        self._running.set()

        while self._running.is_set():
            request = self.transport.recv_request()
            if request is None:
                # server is down, return to avoid infinite loop
                return

            self.pool.submit(self._handle_request, request)

    def _handle_request(self, request):

        def get_resource_and_method(location, method):
            resource = self.resources.get(location)
            if not resource:
                return None, None

            instance = resource.instance
            method_getter = operator.attrgetter(method)

            try:
                method = method_getter(instance)
                return resource, method
            except AttributeError:
                return resource, None

        resource, method = get_resource_and_method(request.location, request.method)
        if not resource:
            self.transport.send_response(
                request,
                self.protocol.not_found(f"Resource {request.location} not found"),
            )
            return None

        if not method:
            self.transport.send_response(
                request, self.protocol.not_found(f"Method {request.method} not found")
            )
            return None

        try:
            result = method(*request.args, **request.kwargs)
            self.transport.send_response(request, self.protocol.ok(result))
        except Exception as e:
            self.transport.send_response(request, self.protocol.error(e))

    def publish(self, topic, *args, **kwargs):
        self.transport.publish(topic, self.protocol.event(*args, **kwargs))
