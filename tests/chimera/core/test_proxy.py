import copy

import pytest

from chimera.core.proxy import Proxy, ProxyMethod
from chimera.core.url import parse_url


class ExplodingBus:
    """Any attribute access means a protocol probe leaked onto the bus."""

    def __getattr__(self, name):
        raise RuntimeError(f"bus touched during copy: {name}")


@pytest.fixture
def proxy():
    # built without __init__ to avoid needing a live Bus; same instance
    # dict shape __init__ produces
    p = Proxy.__new__(Proxy)
    p.__dict__.update(
        {
            "__url__": parse_url("tcp://localhost:7777/Telescope/tel"),
            "__resolved_url__": parse_url("tcp://localhost:7778/Telescope/tel"),
            "__proxy_url__": parse_url("tcp://localhost:7777/Proxy/p"),
            "__bus__": ExplodingBus(),
            "__timeout__": None,
        }
    )
    return p


class TestProxyCopy:
    def test_dunder_probes_raise(self, proxy):
        """copy/pickle probe dunders via getattr: they must see a plain
        AttributeError, never a phantom remote ProxyMethod."""
        assert not hasattr(proxy, "__setstate__")
        assert not hasattr(proxy, "__getnewargs_ex__")
        assert not hasattr(proxy, "__fspath__")

    def test_regular_attributes_still_remote(self, proxy):
        assert isinstance(proxy.abort_slew, ProxyMethod)

    def test_copy_is_new_handle_same_bus(self, proxy):
        clone = copy.copy(proxy)

        assert clone is not proxy
        assert clone.__dict__ == proxy.__dict__
        assert clone.__bus__ is proxy.__bus__
        assert isinstance(clone.abort_slew, ProxyMethod)

    def test_deepcopy_never_copies_the_bus(self, proxy):
        clone = copy.deepcopy(proxy)

        assert clone is not proxy
        assert clone.__bus__ is proxy.__bus__
        assert isinstance(clone.abort_slew, ProxyMethod)
