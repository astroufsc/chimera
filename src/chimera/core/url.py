import uuid
from dataclasses import dataclass
from functools import cached_property
from urllib.parse import urlsplit


class URLInvalidHostError(ValueError):
    pass


class URLInvalidPathError(ValueError):
    pass


@dataclass(frozen=True)
class URL:
    raw: str

    bus: str  # tcp://host:port
    host: str
    port: int

    path: str  # /<cls>/<name>
    cls: str
    name: str

    indexed: bool

    @cached_property
    def url(self) -> str:
        return f"{self.bus}{self.path}"

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f"URL(bus={self.bus!r}, path={self.path!r})"


def parse_url(url: str | URL) -> URL:
    if isinstance(url, URL):
        return url

    # urlsplit needs the URL to have a scheme, otherwise if will join netloc and path as path
    if not url.startswith("tcp://"):
        url = f"tcp://{url}"

    parts = urlsplit(url)

    host, port = parse_host(parts.netloc)
    cls, name = parse_path(parts.path)
    indexed = isinstance(name, int)

    return URL(
        raw=url,
        bus=f"tcp://{host}:{port}",
        host=host,
        port=port,
        path=f"/{cls}/{name}",
        cls=cls,
        name=str(name),
        indexed=indexed,
    )


def parse_host(host: str) -> tuple[str, int]:
    parts = host.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid host '{host}': host must be in the format '[tcp://]<host>:<port>'"
        )

    host, port = parts

    if host == "" or " " in host:
        raise ValueError(
            f"Invalid host '{host}': host name is empty or contains spaces"
        )

    try:
        port = int(port)
    except ValueError:
        raise ValueError(f"Invalid port '{host}': port is not a valid integer")

    return host, port


def parse_path(path: str) -> tuple[str, int | str]:
    if not path.startswith("/"):
        raise ValueError(f"Invalid path '{path}': path does not start with '/'")

    parts = path.split("/")
    if len(parts) < 3:
        raise ValueError(
            f"Invalid path '{path}': path is not in the format '/<class>/<name|index>'"
        )

    _, cls, name = parts

    if cls == "" or "$" in cls or " " in cls:
        raise ValueError(f"Invalid path '{path}': class is empty or contains spaces")

    if name == "" or " " in name:
        raise ValueError(f"Invalid path '{path}': name is empty or contains spaces")

    if name[0].isdigit():
        try:
            return cls, int(name)
        except ValueError:
            pass

    # not a numbered instance
    return cls, name


def create_url(bus: URL, cls: str, name: str | int | None = None) -> URL:
    if name is None:
        name = uuid.uuid4().hex

    path = f"/{cls}/{name}"
    return parse_url(f"{bus.url}{path}")


def resolve_url(url: str, bus: str | URL) -> URL:
    """Resolves a possibly relative URL against a bus URL.

    If the given URL is already absolute, it is returned as-is.
    If it is relative (i.e., missing host/port), it is combined with the bus URL.

    Args:
        url: The URL to resolve, either absolute or relative.
        bus: The bus URL to use for resolution if `url` is relative.

    Returns:
        The resolved absolute URL.
    """
    if url.startswith("tcp://" or not url.startswith("/")):
        return parse_url(url)

    bus_url = parse_url(bus)

    return parse_url(f"{bus_url.url}{url}")
