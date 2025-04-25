import time
from rich import print

from chimera.core.proxy import Proxy
from chimera.core.location import Location


def test_proxy_bench():
    telescope = Proxy(
        Location(host="127.0.0.1", port=8088, cls="FakeTelescope", name="0")
    )

    # telescope.__getitem__("device")
    # p = telescope.get_position_ra_dec()
    # # inspect(p)

    N = 10000

    t0 = time.time()

    for i in range(N):
        telescope.is_parked()

    total = time.time() - t0
    us_per_call = (total * 1e6) / N

    print(f"{N=} {total:.3f} s total, {us_per_call:.3f} us per, call rps={N/total:.3f}")
