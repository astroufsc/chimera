from collections.abc import Callable
from typing import Any

from chimera.core.bus import Bus
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.url import URL, create_url, parse_url, resolve_url

__all__ = ["Proxy", "ProxyMethod"]


class Proxy:
    def __init__(self, url: str | URL, bus: Bus):
        self.__url__ = parse_url(url)
        self.__resolved_url__: URL | None = None
        self.__proxy_url__ = create_url(bus=bus.url.bus, cls="Proxy")
        self.__bus__ = bus

    def resolve(self) -> None:
        if self.__resolved_url__ is not None:
            return

        self.ping()

        if not self.__resolved_url__:
            raise ObjectNotFoundException(f"could not resolve proxy for {self.__url__}")

    def ping(self) -> bool:
        pong = self.__bus__.ping(src=self.__proxy_url__, dst=self.__url__)
        if pong is None:
            raise RuntimeError("bus is dead")
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
        return ProxyMethod(self, attr)

    def __getitem__(self, item: str):
        return ProxyMethod(self, "__getitem__")(item)

    def __setitem__(self, item: str, value: Any):
        return ProxyMethod(self, "__setitem__")(item, value)

    def __iadd__(self, config_dict: dict[str, Any]):
        ProxyMethod(self, "__iadd__")(config_dict)
        return self

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
        return f"<{self.proxy.__proxy_url__}.{self.method} method proxy at {hex(hash(self))}>"

    def __str__(self):
        return f"[method proxy for {self.proxy.__proxy_url__} {self.method} method]"

    # synchronous call
    def __call__(self, *args: Any, **kwargs: Any):
        # this is not thread safe
        self.proxy.resolve()
        assert self.proxy.__resolved_url__ is not None

        response = self.proxy.__bus__.request(
            src=self.proxy.__proxy_url__.url,
            dst=self.proxy.__resolved_url__,
            method=self.method,
            # FIXME: requests should use tuple
            args=list(args),
            kwargs=kwargs,
        )

        # FIXME: bus should not return None, either good or error
        if response is None:
            raise RuntimeError("bus is dead")

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
