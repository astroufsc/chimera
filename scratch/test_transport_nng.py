from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.protocol import Protocol
from chimera.core.transport_nng import TransportNNG

from rich import print

proto = Protocol()
# request = proto.request("localhost:8088/Foo/foo", "bar", (2, 2), {})

transport = TransportNNG("127.0.0.1", 8088, PickleSerializer)
transport.bind()

request = transport.recv_request()
print(request)

transport.send_response(request, proto.ok("Hello"))
