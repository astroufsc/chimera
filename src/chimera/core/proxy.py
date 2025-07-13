import inspect
import threading
from chimera.core.client import Client
from chimera.core.location import Location

import logging


__all__ = ["Proxy", "ProxyMethod"]


log = logging.getLogger(__name__)


class Proxy:

    def __init__(self, location):
        self.location: Location = Location(location)
        self.client: Client = Client(self.location)
        self._original_thread = threading.current_thread().native_id

    def __getstate__(self):
        return {
            "location": self.__dict__["location"],
            "_original_thread": self._original_thread,
        }

    def __setstate__(self, state):
        location = state["location"]
        log.warning(f"Recreating proxy object for {location}")

        setattr(self, "location", location)
        setattr(self, "client", Client(location))
        setattr(self, "_original_thread", state["_original_thread"])

    def ping(self):
        if threading.current_thread().native_id != self._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        return self.client.ping()

    def publish_event(self, topic: str, args, kwargs):
        if threading.current_thread().native_id != self._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        return self.client.publish_event(topic, args, kwargs)

    def subscribe_event(self, topic, handler):
        if threading.current_thread().native_id != self._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        self.client.subscribe_event(topic, handler)

    def unsubscribe_event(self, topic, handler):
        if threading.current_thread().native_id != self._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        self.client.unsubscribe_event(topic, handler)

    def __getnewargs__(self):
        return tuple()

    def __getattr__(self, attr):
        return ProxyMethod(self, attr)

    def __getitem__(self, item):
        return ProxyMethod(self, "__getitem__")(item)

    def __setitem__(self, item, value):
        return ProxyMethod(self, "__setitem__")(item, value)

    def __iadd__(self, config_dict):
        ProxyMethod(self, "__iadd__")(config_dict)
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
        if threading.current_thread().native_id != self.proxy._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        return self.proxy.client.request(self.method, args, kwargs)

    # event handling
    def __iadd__(self, other):
        if threading.current_thread().native_id != self.proxy._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        topic = f"{self.proxy.location}/{self.method}"
        self.proxy.client.subscribe_event(topic, other)
        return self

    def __isub__(self, other):
        if threading.current_thread().native_id != self.proxy._original_thread:
            log.warning(
                f"{inspect.stack()[0][3]}: Proxy object is being used in a different thread"
            )
        topic = f"{self.proxy.location}/{self.method}"
        self.proxy.client.unsubscribe_event(topic, other)
        return self
