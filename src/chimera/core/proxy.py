import pickle
import uuid

import redis

from chimera.core.constants import EVENTS_PROXY_NAME
from chimera.core.location import Location

import logging


__all__ = ['Proxy',
           'ProxyMethod']

log = logging.getLogger(__name__)


class Proxy:

    def __init__(self, location):
        self.location = Location(location)
        self.r = redis.Redis(
            host=self.location.host,
            port=self.location.port,
        )


    def __getstate__(self):
        return {"location": self.__dict__["location"]}

    def __setstate__(self, state):
        location = state["location"]

        setattr(self, "location", location)
        setattr(self, "r", redis.Redis(host=location.host, port=location.port))

    def ping(self):
        return self.r.ping()

    def __getnewargs__(self):
        return tuple()

    def __getattr__(self, attr):
        return ProxyMethod(self, attr)

    def __getitem__(self, item):
        return ProxyMethod(self, "__getitem__")(item)

    def __setitem__(self, item, value):
        return ProxyMethod(self, "__setitem__")(item,value)

    def __iadd__(self, configDict):
        ProxyMethod(self, "__iadd__")(configDict)
        return self

    def __repr__(self):
        return "<%s proxy at %s>" % (self.location, hex(id(self)))

    def __str__(self):
        return "[proxy for %s]" % self.location


class ProxyMethod (object):

    def __init__(self, proxy, method):

        self.proxy = proxy
        self.method = method
        self.sender = self._invoke

        self.__name__ = method

    def _invoke(self, method, args, kwargs):
        request = {
            "id": uuid.uuid4().hex,
            "version": 1,
            "location": str(self.proxy.location),
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }

        request_key = f"chimera_request"
        response_key = f"chimera_response_{request['id']}"

        self.proxy.r.rpush(request_key, pickle.dumps(request))
        data = self.proxy.r.brpop(response_key, timeout=5*60)
        if data is None:
            raise Exception("Timeout waiting for response")

        _, response_bytes = data
        response = pickle.loads(response_bytes)
        if response.get("error"):
            raise Exception(response["message"])

        return response["result"]

    def __repr__(self):
        return "<%s.%s method proxy at %s>" % (self.proxy.location,
                                               self.method,
                                               hex(hash(self)))

    def __str__(self):
        return "[method proxy for %s %s method]" % (self.proxy.location,
                                                    self.method)

    # synchronous call, just call method using our sender adapter
    def __call__(self, *args, **kwargs):
        # print("Proxy.__call__ @ %s:%s : %s with args %s and kwargs %s" % (self.proxy.location.host, self.proxy.location.port, self.method, args, kwargs))
        return self.sender(self.method, args, kwargs)

    # async pattern
    def begin(self, *args, **kwargs):
        return self.sender("%s.begin" % self.method, args, kwargs)

    def end(self, *args, **kwargs):
        return self.sender("%s.end" % self.method, args, kwargs)

    # event handling

    def __do(self, other, action):

        handler = {"topic": self.method,
                   "handler": {"proxy": "",
                               "method": ""}
                   }

        # REMEMBER: Return a copy of this wrapper as we are using +=

        # Can't add itself as a subscriber
        if other == self:
            return self

        # passing a proxy method?
        if not isinstance(other, ProxyMethod):
            log.debug("Invalid parameter: %s" % other)
            raise TypeError("Invalid parameter: %s" % other)

        handler["handler"]["proxy"] = other.proxy.URI
        handler["handler"]["method"] = str(other.__name__)

        try:
            self.sender("%s.%s" % (EVENTS_PROXY_NAME, action), (handler,), {})
        except Exception:
            log.exception("Cannot %s to topic '%s' using proxy '%s'." %
                         (action, self.method, self.proxy))

        return self

    def __iadd__(self, other):
        return self.__do(other, "subscribe")

    def __isub__(self, other):
        return self.__do(other, "unsubscribe")
