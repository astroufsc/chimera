from .transport import Transport
from .transport_nng import TransportNNG


def create_transport(url: str) -> Transport:
    return TransportNNG(url)
