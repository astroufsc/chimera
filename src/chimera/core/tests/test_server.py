from chimera.core.resources import ResourcesManager
from chimera.core.server import Server


class Foo:
    def bar(self, a, b):
        print(self, a, b)
        return a + b


res = ResourcesManager()
res.add("127.0.0.1:8088/Foo/foo", Foo())

s = Server(res, "127.0.0.1", 8088)
s.start()
s.loop()
