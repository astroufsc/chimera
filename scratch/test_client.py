from rich import print
from chimera.core.client import Client
from chimera.core.location import Location


c = Client(Location("127.0.0.1:8088/Foo/foo"))
c.ping()

response = c.request(
    method="bar",
    args=(2, 4),
    kwargs={},
)

print(response)
