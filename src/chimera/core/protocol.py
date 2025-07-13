import traceback
import uuid
from dataclasses import dataclass
from typing import Any
from .serializer import Serializable


@dataclass
class Request(Serializable):
    id: str
    version: int
    location: str
    method: str
    args: list[Any]
    kwargs: dict[str, Any]


@dataclass
class Event(Serializable):
    id: str
    version: int
    location: str
    args: list[Any]
    kwargs: dict[str, Any]


@dataclass
class Response(Serializable):
    id: str
    code: int

    result: Any | None = None
    error: str | None = None


class Protocol:
    def new_id(self):
        return uuid.uuid4().hex

    def request(self, location, method, args, kwargs) -> Request:
        return Request(
            id=self.new_id(),
            version=1,
            location=str(location),
            method=method,
            args=args,
            kwargs=kwargs,
        )

    def event(self, location, args, kwargs) -> Event:
        return Event(
            id=self.new_id(),
            version=1,
            location=str(location),
            args=args,
            kwargs=kwargs,
        )

    def ok(self, result: Any) -> Response:
        return Response(
            id=self.new_id(),
            code=200,
            result=result,
        )

    def error(self, e) -> Response:
        tb = "".join(traceback.format_exception(e))
        return Response(
            id=self.new_id(),
            code=500,
            error=f"{e.__class__.__name__}: {str(e)} (traceback={tb})",
        )

    def not_found(self, msg: str) -> Response:
        return Response(
            id=self.new_id(),
            code=404,
            error=msg,
        )
