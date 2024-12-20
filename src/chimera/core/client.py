from chimera.core.location import Location
from chimera.core.protocol import Protocol
from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.transport_redis import RedisTransport


class Client:
    def __init__(
        self,
        location: Location,
        protocol=Protocol,
        transport=RedisTransport,
        serializer=PickleSerializer,
    ):
        self.location = location
        self.protocol = protocol()
        self.transport = transport(location.host, location.port, serializer)
        self.transport.connect()

    def ping(self):
        return self.transport.ping()

    # start in protocol and handle to bytes
    def request(self, method, args, kwargs, timeout=None):
        request = self.protocol.request(
            location=self.location,
            method=method,
            args=args,
            kwargs=kwargs,
        )

        self.transport.send_request(request)

        # FIXME: timeout should be configurable, calls can take a long time.
        response = self.transport.recv_response(request)
        if response is None:
            raise Exception("Server is down")

        if response.error:
            raise Exception(response.error)

        return response.result
