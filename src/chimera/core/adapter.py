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

    @abstractmethod
    def connect(self, obj, location, index=None):
        pass

    @abstractmethod
    def disconnect(self, obj):
        pass

    @abstractmethod
    def shutdown(self, disconnect):
        pass

    @abstractmethod
    def requestLoop(self):
        pass


class RedisAdapter(Adapter):

    def __init__(self, manager, host, port):
        super().__init__(manager, host, port)

        self.r = redislite.Redis(serverconfig={"bind": host, "port": port})
        self.key = "chimera_request"

    def connect(self, obj, location, index=None):
        return location

    def disconnect(self, obj):
        pass

    def shutdown(self, disconnect):
        self.r.shutdown()

    def requestLoop(self):
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
