import operator
import pickle
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor

import redis
import redislite


class ChimeraProtocol:
    REQUESTS_KEY: str = "chimera_requests"

    DEFAULT_TIMEOUT: int = 5 * 60  # 5 minutes
    LOOP_TICK: int = 1

    def response_key(self, request):
        return f"chimera_response_{request['id']}"

    def id(self):
        return uuid.uuid4().hex

    def request(self, location, method, args, kwargs):
        return {
            "id": self.id(),
            "version": 1,
            "location": str(location),
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }

    def ok(self, result):
        return {
            "id": self.id(),
            "result": result,
        }


    def error(self, e):
        return {
            "id": self.id(),
            "error": e.__class__.__name__,
            "message": str(e),
            "stack": traceback.format_exc(),
        }

    def not_found(self, method):
        return {
            "id": self.id(),
            "error": "AttributeError",
            "message": f"Method {method} not found",
        }


class RedisTransport:

    def __init__(self, host, port):
        self.r = redislite.Redis(serverconfig={"bind": host, "port": port})

    def start(self):
        self.r.delete(self.protocol.REQUESTS_KEY)

    def ping(self):
        return self.r.ping()

    def stop(self):
        self.r.shutdown()

    def write(self, response_bytes):
        self.r.lpush(self.protocol.response_key(request), response_bytes)

    def read(self):
        try:
            return self.r.blpop((self.protocol.REQUESTS_KEY,),  self.protocol.LOOP_TICK)
        except redis.exceptions.ConnectionError:
            return None


class PickleSerializer:

    def dumps(self, obj):
        return pickle.dumps(obj)

    def loads(self, data):
        return pickle.loads(data)


class Server:
    def __init__(self, manager, host, port, protocol=ChimeraProtocol, transport=RedisTransport, serializer=PickleSerializer, pool=ThreadPoolExecutor):
        super().__init__(manager, host, port)
        self.transport = transport(host, port)
        self.pool = pool()
        self.protocol = protocol()
        self.serializer = serializer()

    def start(self):
        self.transport.start()
        self.pool.submit(self.loop)

    def stop(self, disconnect):
        self.transport.stop()

    def ping(self):
        return self.transport.ping()

    def loop(self):
        while True:
            msg = self.transport.read()
            if not msg:
                continue

            self.pool.submit(self._handle_request, msg)

    # protocol
    def _handle_request(self, request):
        _, request_bytes = request
        msg = self.serializer.loads(request_bytes)
        response = self._handle_message(msg)
        response_bytes = self.serializer.dumps(response)
        self.transport.write(response_bytes)

    def _handle_message(self, msg):
        resource = self.manager.getInstance(msg["location"])
        if not resource:
            return self.protocol.not_found(msg['location'])

        instance = resource.instance
        method_getter = operator.attrgetter(msg["method"])

        try:
            method = method_getter(instance)
        except AttributeError:
            return self.protocol.not_found(msg['method'])

        try:
            result = method(*msg["args"], **msg["kwargs"])
            return self.protocol.ok(result)
        except Exception as e:
            return self.protocol.error(e)


class Client:
    def __init__(self, location):
        self._r = None
        self.location = location

    @property
    def r(self):
        if not self._r:
            self._r = redis.Redis(self.location.host, self.location.port)
        return self._r

    def ping(self):
        return self.r.ping()

    # start in protocol and handle to bytes
    def request(self, method, args, kwargs, timeout=None):
        request = ChimeraProtocol.request(
            location=self.location,
            method=method,
            args=args,
            kwargs=kwargs,
        )

        self.r.rpush(ChimeraProtocol.REQUESTS_KEY, pickle.dumps(request))
        # FIXME: timeout should be configurable, calls can take a long time.
        data = self.r.brpop([ChimeraProtocol.response_key(request)], timeout=timeout or ChimeraProtocol.DEFAULT_TIMEOUT)
        if data is None:
            raise Exception("Timeout waiting for response")

        _, response_bytes = data

        response = pickle.loads(response_bytes)
        if response.get("error"):
            raise Exception(response["message"])

        return response["result"]


def create_server(host, port, protocol="redis"):
    if protocol == "redis":
        return Server(None, host, port)
    else:
        raise ValueError(f"Protocol {protocol} not supported")

def create_client(host, port, protocol="redis"):
    if protocol == "redis":
        return Client(None, host, port)
    else:
        raise ValueError(f"Protocol {protocol} not supported")
