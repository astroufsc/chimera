from chimera.core.client import Client
from chimera.core.constants import EVENTS_PROXY_NAME
from chimera.core.location import Location

import logging


__all__ = ["Proxy", "ProxyMethod"]


log = logging.getLogger(__name__)


class Proxy:

    def __init__(self, location):
        self.location = Location(location)
        self.client = Client(self.location)

    def __getstate__(self):
        return {"location": self.__dict__["location"]}

    def __setstate__(self, state):
        location = state["location"]

        setattr(self, "location", location)
        setattr(self, "client", Client(location))

    def ping(self):
        return self.client.ping()

    def publish_event(self, topic: str, args, kwargs):
        return self.client.publish_event(topic, args, kwargs)

    def __getnewargs__(self):
        return tuple()

    def __getattr__(self, attr):
        return ProxyMethod(self, attr)

    def __getitem__(self, item):
        return ProxyMethod(self, "__getitem__")(item)

    def __setitem__(self, item, value):
        return ProxyMethod(self, "__setitem__")(item, value)

    def __iadd__(self, configDict):
        ProxyMethod(self, "__iadd__")(configDict)
        return self

    def __repr__(self):
        return f"<{self.location} proxy at {hex(id(self))}>"

    def __str__(self):
        return f"[proxy for {self.location}]"


class ProxyMethod(object):

    def __init__(self, proxy, method):

        self.proxy = proxy
        self.method = method

        self.__name__ = method

    def __repr__(self):
        return (
            f"<{self.proxy.location}.{self.method} method proxy at {hex(hash(self))}>"
        )

    def __str__(self):
        return f"[method proxy for {self.proxy.location} {self.method} method]"

    # synchronous call
    def __call__(self, *args, **kwargs):
        return self.proxy.client.request(self.method, args, kwargs)

    # async pattern begin
    def begin(self, *args, **kwargs):
        return self.proxy.client.request(f"{self.method}.begin", args, kwargs)

    # async pattern end
    def end(self, *args, **kwargs):
        return self.proxy.client.request(f"{self.method}.end", args, kwargs)

    # event handling

    def __do(self, other, action):

        handler = {"topic": self.method, "handler": {"proxy": "", "method": ""}}

        # REMEMBER: Return a copy of this wrapper as we are using +=

        # Can't add itself as a subscriber
        if other == self:
            return self

        # passing a proxy method?
        if not isinstance(other, ProxyMethod):
            log.debug(f"Invalid parameter: {other}")
            raise TypeError(f"Invalid parameter: {other}")

        handler["handler"]["proxy"] = other.proxy.location
        handler["handler"]["method"] = str(other.__name__)

        try:
            self.proxy.client.request(f"{EVENTS_PROXY_NAME}.{action}", (handler,), {})
        except Exception:
            log.exception(
                f"Cannot {action} to topic '{self.method}' using proxy '{self.proxy}'."
            )

        return self

    def __iadd__(self, other):
        return self.__do(other, "subscribe")

    def __isub__(self, other):
        return self.__do(other, "unsubscribe")
