import orjson as json

from typing import override

from chimera.core.serializer import Serializer


class JSONSerializer(Serializer):

    @override
    def dumps(self, obj):
        return json.dumps(obj)

    @override
    def loads(self, data):
        return json.loads(data)

    @property
    @override
    def object_mode(self) -> bool:
        return False
