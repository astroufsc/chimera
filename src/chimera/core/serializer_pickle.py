import pickle

from chimera.core.serializer import Serializer


class PickleSerializer(Serializer):
    def dumps(self, obj):
        return pickle.dumps(obj)

    def loads(self, data):
        return pickle.loads(data)
