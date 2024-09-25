from chimera.core.serializer_pickle import *
from chimera.core.protocol import *
from chimera.core.transport_redis import *

from rich import print

proto = Protocol()
r = proto.request("localhost:8088/Foo/foo", "bar", (2, 2), {})

transport = RedisTransport(PickleSerializer(), "localhost", 8088)

transport.send_request(r)

request = transport.recv_request()
print(request)
