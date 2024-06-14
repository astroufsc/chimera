import abc
import operator
import pickle
import traceback
import uuid
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor

import redis
import redislite


class Adapter(abc.ABC):

    def __init__(self, manager, host, port):
        self.manager = manager
        self.host = host
        self.port = port

    def ping(self):
        return "PONG"

    @abstractmethod
    def connect(self, obj, location):
        pass

    @abstractmethod
    def disconnect(self, obj):
        pass

    @abstractmethod
    def shutdown(self, disconnect):
        pass

    @abstractmethod
    def request_loop(self):
        pass


def create_adapter(host, port, protocol="redis"):
    if protocol == "redis":
        return RedisAdapter(None, host, port)
    else:
        raise ValueError(f"Protocol {protocol} not supported")


class RedisAdapter(Adapter):

    def __init__(self, manager, host, port):
        super().__init__(manager, host, port)

        if manager is None:
            self.r = redis.Redis(host, port)
        else:
            self.r = redislite.Redis(serverconfig={"bind": host, "port": port})

        self.key = "chimera_request"

    def ping(self):
        return self.r.ping()

    def connect(self, obj, location):
        return location

    def disconnect(self, obj):
        pass

    def shutdown(self, disconnect):
        self.r.shutdown()

    def call(self, location, method, args, kwargs):
        request = {
            "id": uuid.uuid4().hex,
            "version": 1,
            "location": str(location),
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }

        request_key = f"chimera_request"
        response_key = f"chimera_response_{request['id']}"

        self.r.rpush(request_key, pickle.dumps(request))
        data = self.r.brpop([response_key], timeout=5*60)
        if data is None:
            raise Exception("Timeout waiting for response")

        _, response_bytes = data
        response = pickle.loads(response_bytes)
        if response.get("error"):
            raise Exception(response["message"])

        return response["result"]

    def request_loop(self):
        self.r.delete(self.key)

        pool = ThreadPoolExecutor()
        queues = [self.key]

        while True:
            try:
                msg = self.r.blpop(queues, 10)
                if not msg:
                    continue
                pool.submit(self.handle_request, msg)
            except redis.exceptions.ConnectionError:
                break

    def handle_request(self, msg):
        _, request_bytes = msg
        request = pickle.loads(request_bytes)

        resource = self.manager.getInstance(request["location"])
        if not resource:
            response = {
                "id": uuid.uuid4().hex,
                "error": "ResourceNotFound",
                "message": f"Resource {request['location']} not found",
            }
        else:
            instance = resource.instance
            method_getter = operator.attrgetter(request["method"])

            try:
                method = method_getter(instance)
            except AttributeError:
                response = {
                    "id": uuid.uuid4().hex,
                    "error": "AttributeError",
                    "message": f"Method {request['method']} not found",
                }
            else:
                try:
                    result = method(*request["args"], **request["kwargs"])
                    response = {
                        "id": uuid.uuid4().hex,
                        "result": result,
                    }
                except Exception as e:
                    response = {
                        "id": uuid.uuid4().hex,
                        "error": e.__class__.__name__,
                        "message": str(e),
                        "stack": traceback.format_exc(),
                    }

        response_key = f"chimera_response_{request['id']}"
        response_bytes = pickle.dumps(response)
        self.r.lpush(response_key, response_bytes)
