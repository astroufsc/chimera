from collections.abc import Callable
from typing import Any, Self

from chimera.core.bus import Bus
from chimera.core.url import URL, create_url, parse_url

__all__ = ["Proxy", "ProxyMethod"]


class Proxy:
    def __init__(self, url: str, bus: Bus):
        if isinstance(url, URL):
            self.__url__ = str(url)
        else:
            self.__url__ = url
        self.__proxy_url__ = create_url(bus=bus.url, cls="Proxy")
        self.__bus__ = bus

    def ping(self) -> bool:
        pong = self.__bus__.ping(src=str(self.__proxy_url__), dst=str(self.__url__))
        if pong is None:
            raise RuntimeError("bus is dead")
        return pong.ok

    def get_proxy(self, url: str) -> Self:
        try:
            u = parse_url(url)
        except ValueError:
            # assume that url only contains the path, so use our bus as the url
            u = parse_url(f"{self.__url__}{url}")
        return Proxy(str(u), self.__bus__)

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
        return f"<{self.location} proxy at {hex(id(self))}>"

    def __str__(self):
        return f"[proxy for {self.location}]"


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
        response = self.proxy.__bus__.request(
            src=str(self.proxy.__proxy_url__),
            dst=self.proxy.__url__,
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
        self.proxy.__bus__.subscribe(
            sub=str(self.proxy.__proxy_url__),
            pub=self.proxy.__url__,
            event=self.method,
            callback=other,
        )
        return self

    def __isub__(self, other: Callable[..., Any]):
        self.proxy.__bus__.unsubscribe(
            sub=str(self.proxy.__proxy_url__),
            pub=self.proxy.__url__,
            event=self.method,
            callback=other,
        )
        return self
