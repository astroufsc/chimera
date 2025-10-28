import pickle
from typing import override

from chimera.core.serializer import Serializer


class PickleSerializer(Serializer):
    @override
    def dumps(self, obj):
        return pickle.dumps(obj)

    @override
    def loads(self, data):
        return pickle.loads(data)

    @property
    @override
    def object_mode(self) -> bool:
        return True
