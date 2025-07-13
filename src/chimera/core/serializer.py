from typing import Self, Type
import logging

logger = logging.getLogger(__name__)


class Serializer:
    def dumps(self, obj) -> bytes | None: ...

    def loads(self, data): ...

    @property
    def object_mode(self) -> bool: ...


class Serializable:
    def dump(self, serializer: Serializer) -> bytes | None:
        try:
            return serializer.dumps(self)
        except Exception:
            # TODO: raise this somehow?
            return None

    @classmethod
    def load(cls: Type[Self], serializer: Serializer, data: bytes) -> Self | None:
        try:
            if serializer.object_mode:
                return serializer.loads(data)
            return cls(**serializer.loads(data))
        except Exception as e:
            logger.error(f"Failed to load {cls.__name__} from data: {data}", exc_info=e)
            return None
