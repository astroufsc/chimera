from chimera.core.location import Location
from chimera.core.protocol import Protocol
from chimera.core.transport_factory import create_transport


class Client:
    def __init__(
        self,
        location: Location,
        protocol=Protocol,
    ):
        self.location = location
        self.protocol = protocol()
        self.transport = create_transport(str(location))
        self.transport.connect()

    def __del__(self):
        self.transport.close()

    def ping(self):
        return self.transport.ping()

    # TODO: implement timeout
    def request(self, method, args, kwargs, timeout=None):
        request = self.protocol.request(
            location=self.location,
            method=method,
            args=args,
            kwargs=kwargs,
        )

        self.transport.send_request(request)

        response = self.transport.recv_response(request)
        # TODO: handle more errors
        # if response is None:
        #     raise Exception("Server is down")
        if response is None:
            raise Exception("Invalid response")

        if response.error:
            raise Exception(response.error)

        return response.result

    def publish_event(self, topic: str, args, kwargs):
        self.transport.publish(topic, self.protocol.event(topic, args, kwargs))

    def subscribe_event(self, topic: str, handler):
        self.transport.subscribe(topic, handler)

    def unsubscribe_event(self, topic: str, handler):
        self.transport.unsubscribe(topic, handler)
