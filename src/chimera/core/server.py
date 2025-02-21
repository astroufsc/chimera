import functools
import operator
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

import pynng

from chimera.core.resources import ResourcesManager
from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.protocol import Protocol
from chimera.core.transport import create_transport
from chimera.core.transport_nng import TransportNNG

log = logging.getLogger(__name__)


class Server:
    def __init__(
        self,
        resources: ResourcesManager,
        host,
        port,
        protocol=Protocol,
        transport=TransportNNG,
        serializer=PickleSerializer,
        pool=ThreadPoolExecutor,
    ):
        self.resources = resources
        self.transport = create_transport(host, port, transport)
        self.pool = pool(thread_name_prefix=f"{host}:{port}/Server")
        self.protocol = protocol()
        self.serializer = serializer()
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

        self.transport._thread_id = threading.current_thread().native_id

        self.q = queue.SimpleQueue()

        while self._running.is_set():
            try:
                # non-blocking recv or selector?
                data = self.transport.recv(block=False)
                self.pool.submit(self._handle_request, data)
            except pynng.exceptions.TryAgain:
                pass

            # if data is None:
            #     # server is down, return to avoid infinite loop
            #     return

            while not self.q.empty():
                print("sending data")
                self.transport.send(self.q.get())

    def get_resource_and_method(self, location, method):
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

    def _handle_request(self, data: bytes):
        request = self.serializer.loads(data)
        if request is None:
            self.q.put(self.serializer.dumps(self.protocol.error("Invalid request")))
            return

        resource, method = self.get_resource_and_method(
            request.location, request.method
        )
        if not resource:
            self.q.put(
                self.serializer.dumps(
                    self.protocol.not_found(f"Resource {request.location} not found")
                )
            )
            return None

        if not method:
            self.q.put(
                self.serializer.dumps(
                    self.protocol.not_found(f"Method {request.method} not found")
                )
            )
            return None

        try:
            result = method(*request.args, **request.kwargs)
            self.q.put(self.serializer.dumps(self.protocol.ok(result)))
        except Exception as e:
            self.q.put(self.serializer.dumps(self.protocol.error(e)))

    def publish(self, topic, *args, **kwargs):
        self.transport.publish(
            topic, self.serializer.dumps(self.protocol.event(*args, **kwargs))
        )
