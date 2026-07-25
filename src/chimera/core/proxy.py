from collections.abc import Callable
from typing import Any

from chimera.core.bus import Bus
from chimera.core.exceptions import (
    BusDeadException,
    ObjectBusyException,
    ObjectNotFoundException,
)
from chimera.core.url import URL, create_url, parse_url, resolve_url

__all__ = ["Proxy", "ProxyMethod"]


class Proxy:
    """A remote-object handle, safe to share between threads.

    Every attribute access builds a fresh ProxyMethod, so calls carry no
    shared state; the only mutable field, __resolved_url__, is set once and
    never invalidated; and the bus correlates replies by message id, so
    concurrent calls through one proxy cannot receive each other's answers.
    """

    def __init__(self, url: str | URL, bus: Bus, timeout: float | None = None):
        self.__url__ = parse_url(url)
        self.__resolved_url__: URL | None = None
        self.__proxy_url__ = create_url(bus=bus.url.bus, cls="Proxy")
        self.__bus__ = bus
        # per-proxy request timeout; None uses the bus default
        self.__timeout__ = timeout

    def resolve(self) -> None:
        if self.__resolved_url__ is not None:
            return

        self.ping()

        if not self.__resolved_url__:
            raise ObjectNotFoundException(f"could not resolve proxy for {self.__url__}")

    def ping(self, timeout: float = 5.0) -> bool:
        pong = self.__bus__.ping(
            src=self.__proxy_url__, dst=self.__url__, timeout=timeout
        )
        if pong is None:
            raise BusDeadException("bus is dead")
        resolved = self.__resolved_url__ is not None
        if not resolved and pong.ok and pong.resolved_url:
            self.__resolved_url__ = parse_url(pong.resolved_url)
        return pong.ok

    def get_proxy(self, url: str) -> "Proxy":
        """Returns a Proxy for a resource relative to this Proxy's URL."""
        resolved_url = resolve_url(url, bus=self.__url__.bus)
        proxy = Proxy(resolved_url, self.__bus__)
        proxy.resolve()
        return proxy

    def __getattr__(self, attr: str):
        # copy/pickle and other protocols probe dunders via getattr: never
        # fabricate remote methods for them (copy.copy would happily call a
        # phantom __setstate__ over the bus)
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        return ProxyMethod(self, attr)

    def __getitem__(self, item: str):
        return ProxyMethod(self, "__getitem__")(item)

    def __setitem__(self, item: str, value: Any):
        return ProxyMethod(self, "__setitem__")(item, value)

    def __iadd__(self, config_dict: dict[str, Any]):
        ProxyMethod(self, "__iadd__")(config_dict)
        return self

    def __copy__(self) -> "Proxy":
        new = Proxy.__new__(Proxy)
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo: dict[int, Any]) -> "Proxy":
        # a Proxy is a handle: a "deep" copy is a new handle to the same
        # remote object on the same live bus, never a copy of the bus
        return self.__copy__()

    def __repr__(self):
        return f"<{self.__url__} proxy at {hex(id(self))}>"

    def __str__(self):
        return f"[proxy for {self.__url__}]"


class ProxyMethod:
    def __init__(self, proxy: Proxy, method: str):
        self.proxy = proxy
        self.method = method

        self.__name__ = method

    def __repr__(self):
        return f"<{self.proxy.__proxy_url__}.{self.method} method proxy at {hex(id(self))}>"

    def __str__(self):
        return f"[method proxy for {self.proxy.__proxy_url__} {self.method} method]"

    def _target_url(self) -> str:
        url = self.proxy.__resolved_url__ or self.proxy.__url__
        return url.url

    def __eq__(self, other: Any):
        """Two ProxyMethods for the same object and method are the same
        logical callback, and so is a bound method of that very object —
        this is what lets `p.event -= s.callback` find the registration
        even though every attribute access creates a fresh object."""
        if isinstance(other, ProxyMethod):
            return (
                self._target_url() == other._target_url()
                and self.method == other.method
            )

        other_self = getattr(other, "__self__", None)
        get_location = getattr(other_self, "get_location", None)
        if callable(get_location) and getattr(other, "__name__", None) == self.method:
            return get_location() == self._target_url()

        # a wrapped chimera method (MethodWrapperDispatcher) of that object
        other_instance = getattr(other, "instance", None)
        other_func = getattr(other, "func", None)
        if other_instance is not None and other_func is not None:
            get_location = getattr(other_instance, "get_location", None)
            if (
                callable(get_location)
                and getattr(other_func, "__name__", None) == self.method
            ):
                try:
                    return get_location() == self._target_url()
                except Exception:
                    return NotImplemented

        return NotImplemented

    def __hash__(self):
        return hash((self._target_url(), self.method))

    # synchronous call
    def __call__(self, *args: Any, **kwargs: Any):
        # concurrent resolves race benignly: __resolved_url__ is set once to
        # the same value, worst case a duplicate ping
        self.proxy.resolve()
        assert self.proxy.__resolved_url__ is not None

        # raises RequestTimeoutException/BusDeadException on failure; a None
        # timeout (the default) waits as long as the operation takes
        response = self.proxy.__bus__.request(
            src=self.proxy.__proxy_url__.url,
            dst=self.proxy.__resolved_url__,
            method=self.method,
            # FIXME: requests should use tuple
            args=list(args),
            kwargs=kwargs,
            timeout=self.proxy.__timeout__,
        )

        if response.code == 503:
            raise ObjectBusyException(response.error)

        if response.error:
            raise Exception(response.error)

        return response.result

    # event handling
    def __iadd__(self, other: Callable[..., Any]):
        self.proxy.resolve()
        assert self.proxy.__resolved_url__ is not None

        self.proxy.__bus__.subscribe(
            sub=self.proxy.__proxy_url__.url,
            pub=self.proxy.__resolved_url__,
            event=self.method,
            callback=other,
        )
        return self

    def __isub__(self, other: Callable[..., Any]):
        self.proxy.resolve()
        assert self.proxy.__resolved_url__ is not None

        self.proxy.__bus__.unsubscribe(
            sub=self.proxy.__proxy_url__.url,
            pub=self.proxy.__resolved_url__,
            event=self.method,
            callback=other,
        )
        return self
