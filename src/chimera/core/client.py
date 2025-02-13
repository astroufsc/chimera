from chimera.core.location import Location
from chimera.core.protocol import Protocol
from chimera.core.serializer_pickle import PickleSerializer
from chimera.core.transport import create_transport
from chimera.core.transport_nng import TransportNNG


class Client:
    def __init__(
        self,
        location: Location,
        protocol=Protocol,
        transport=TransportNNG,
        serializer=PickleSerializer,
    ):
        self.location = location
        self.protocol = protocol()
        self.serializer = serializer()
        self.transport = create_transport(location.host, location.port, transport)
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

        self.transport.send(self.serializer.dumps(request))

        response = self.transport.recv()
        if response is None:
            raise Exception("Server is down")

        response = self.serializer.loads(response)
        if response is None:
            raise Exception("Invalid response")

        if response.error:
            raise Exception(response.error)

        return response.result

    def publish_event(self, topic, args, kwargs):
        data = self.protocol.event(topic, args, kwargs)
        return self.transport.publish(topic, self.serializer.dumps(data))

    def subscribe_event(self, topic, handler):
        return self.transport.subscribe(topic, handler)

    def unsubscribe_event(self, topic, handler):
        return self.transport.unsubscribe(topic, handler)
