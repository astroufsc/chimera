from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy
from chimera.core.event import event

import time
import math


class Publisher(ChimeraObject):

    def __init__(self):
        ChimeraObject.__init__(self)
        self.counter = 0

    def __start__(self):
        # ATTENTION: get_proxy works only after __init__
        self.foo_done += self.foo_done_clbk
        return True

    def __stop__(self):
        self.foo_done -= self.foo_done_clbk

    def foo(self):
        self.foo_done(time.time())
        return 42

    @event
    def foo_done(self, when):
        pass

    def foo_done_clbk(self, when):
        self.counter += 1

    def get_counter(self):
        return self.counter


class Subscriber(ChimeraObject):

    def __init__(self):
        ChimeraObject.__init__(self)
        self.counter = 0
        self.results = []

    def foo_done_clbk(self, when):
        self.results.append((when, time.time()))
        self.counter += 1
        assert when, "When it happened?"

    def get_counter(self):
        return self.counter

    def get_results(self):
        return self.results


class TestEvents:

    def test_publish(self, manager):

        assert manager.add_class(Publisher, "p") is not False
        assert manager.add_class(Subscriber, "s") is not False

        p = manager.get_proxy("/Publisher/p")
        assert isinstance(p, Proxy)

        s = manager.get_proxy("/Subscriber/s")
        assert isinstance(s, Proxy)

        p.foo_done += s.foo_done_clbk

        assert p.foo() == 42
        time.sleep(0.5)  # delay to get messages delivered
        assert s.get_counter() == 1
        assert p.get_counter() == 1

        assert p.foo() == 42
        time.sleep(0.5)  # delay to get messages delivered
        assert s.get_counter() == 2
        assert p.get_counter() == 2

        # unsubscribe
        p.foo_done -= s.foo_done_clbk
        p.foo_done -= p.foo_done_clbk

        assert p.foo() == 42
        time.sleep(0.5)  # delay to get messages delivered
        assert s.get_counter() == 2
        assert p.get_counter() == 2

    def test_performance(self, manager):

        assert manager.add_class(Publisher, "p") is not False
        assert manager.add_class(Subscriber, "s") is not False

        p = manager.get_proxy("/Publisher/p")
        assert isinstance(p, Proxy)

        s = manager.get_proxy("/Subscriber/s")
        assert isinstance(s, Proxy)

        p.foo_done += s.foo_done_clbk

        for check in range(1):

            start = time.time()
            for i in range(100):
                p.foo()
            end = time.time()

            time.sleep(5)

            results = s.get_results()

            dt = [(t - t0) * 1000 for t0, t in results]
            mean = sum(dt) / len(dt)

            sigma = math.sqrt(sum([(t - mean) ** 2 for t in dt]) / len(dt))

            print("#" * 25)
            print(f"# {len(dt)} events ({end - start:.3f} s)")
            print(f"# {len(dt) / (end - start):.2f} events/s")
            print(f"# min   : {min(dt):<6.3f} ms")
            print(f"# max   : {max(dt):<6.3f} ms")
            print(f"# mean  : {mean:<6.3f} ms")
            print(f"# sigma : {sigma:<6.3f} ms")
            print("#" * 25)
