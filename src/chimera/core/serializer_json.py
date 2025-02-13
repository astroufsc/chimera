import orjson as json

from chimera.core.serializer import Serializer


class JSONSerializer(Serializer):
    def dumps(self, obj):
        return json.dumps(obj)

    def loads(self, data):
        return json.loads(data)
