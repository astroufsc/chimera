import time
import sys

from rich import print, inspect

from chimera.core.proxy import Proxy
from chimera.core.location import Location

telescope = Proxy(Location(host="127.0.0.1", port=9000, cls="FakeTelescope", name="0"))

# telescope.__getitem__("device")
# p = telescope.getPositionRaDec()
# # inspect(p)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

t0 = time.time()

for i in range(N):
    telescope.isParked()

total = time.time() - t0
us_per_call = (total * 1e6) / N

print(f"{N=} {total:.3f} s total, {us_per_call:.3f} us per call")
