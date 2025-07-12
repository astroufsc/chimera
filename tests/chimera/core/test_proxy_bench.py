import time

from rich import print

from chimera.core.bus import Bus
from chimera.core.proxy import Proxy


def test_proxy_bench():
    bus = Bus("tcp://127.0.0.1:9001")
    # TODO: raise if proxy cannot be reached?
    telescope = Proxy("tcp://127.0.0.1:9000/Telescope/0", bus=bus)

    N = 1_000

    t0 = time.monotonic()

    for i in range(N):
        telescope.is_parked()

    total = time.monotonic() - t0
    us_per_call = (total * 1e6) / N

    print(
        f"{N=} {total:.3f} s total, {us_per_call:.3f} us per, call rps={N / total:.3f}"
    )
