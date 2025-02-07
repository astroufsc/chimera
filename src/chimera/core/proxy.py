from chimera.core.client import Client
from chimera.core.location import Location

import logging


__all__ = ["Proxy", "ProxyMethod"]


log = logging.getLogger(__name__)


class Proxy:

    def __init__(self, location):
        self.location: Location = Location(location)
        self.client: Client = Client(self.location)

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

    def subscribe_event(self, topic, handler):
        self.client.subscribe_event(topic, handler)

    def unsubscribe_event(self, topic, handler):
        self.client.unsubscribe_event(topic, handler)

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

    def __init__(self, proxy: Proxy, method: str):

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
    def __iadd__(self, other):
        topic = f"{self.proxy.location}/{self.method}"
        self.proxy.client.subscribe_event(topic, other)
        return self

    def __isub__(self, other):
        topic = f"{self.proxy.location}/{self.method}"
        self.proxy.client.unsubscribe_event(topic, other)
        return self
