
from chimera.core.manager        import Manager
from chimera.core.chimeraobject  import ChimeraObject
from chimera.core.proxy          import Proxy
from chimera.core.event          import event

from nose.tools import assert_raises

import time
import math

class Publisher (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)
        self.counter = 0

    def __start__ (self):
        # ATTENTION: getProxy works only after __init__
        self.fooDone += self.getProxy().fooDoneClbk
        return True

    def __stop__ (self):
        self.fooDone -= self.getProxy().fooDoneClbk

    def foo (self):
        self.fooDone(time.time())
        return 42

    @event
    def fooDone (self, when):
        pass

    def fooDoneClbk (self, when):
        self.counter += 1

    def getCounter (self):
        return self.counter

class Subscriber (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)
        self.counter = 0
        self.results = []

    def fooDoneClbk (self, when):
        self.results.append((when, time.time()))
        self.counter += 1
        assert when, "When it happened?"

    def getCounter (self):
        return self.counter

    def getResults (self):
        return self.results


class TestEvents (object):

    def setup (self):
        self.manager = Manager()

    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_publish (self):

        assert self.manager.addClass (Publisher, "p") != False
        assert self.manager.addClass (Subscriber, "s") != False

        p = self.manager.getProxy("/Publisher/p")
        assert isinstance(p, Proxy)
        
        s = self.manager.getProxy("/Subscriber/s")
        assert isinstance(s, Proxy)

        p.fooDone += s.fooDoneClbk

        assert p.foo() == 42
        time.sleep (0.5) # delay to get messages delivered
        assert s.getCounter() == 1
        assert p.getCounter() == 1

        assert p.foo() == 42
        time.sleep (0.5) # delay to get messages delivered
        assert s.getCounter() == 2
        assert p.getCounter() == 2        

        # unsubscribe
        p.fooDone -= s.fooDoneClbk
        p.fooDone -= p.fooDoneClbk        
        
        assert p.foo() == 42
        time.sleep (0.5) # delay to get messages delivered
        assert s.getCounter() == 2
        assert p.getCounter() == 2        

    def test_performance (self):

        assert self.manager.addClass (Publisher, "p") != False
        assert self.manager.addClass (Subscriber, "s") != False

        p = self.manager.getProxy("/Publisher/p")
        assert isinstance(p, Proxy)
        
        s = self.manager.getProxy("/Subscriber/s")
        assert isinstance(s, Proxy)

        p.fooDone += s.fooDoneClbk

        for check in range (1):

            start = time.time()
            for i in range (100):
                p.foo()
            end = time.time()

            time.sleep (5)

            results = s.getResults()

            dt   = [ (t - t0)*1000 for t0, t in results]
            mean = sum (dt) / len(dt)
        
            sigma = math.sqrt(sum([ (t - mean)**2 for t in dt]) / len(dt))

            print "#"*25
            print "# %d events (%.3f s)" % (len(dt), (end-start))
            print "# %.2f events/s" % (len(dt)/(end-start))
            print "# min   : %-6.3f ms" % min(dt)
            print "# max   : %-6.3f ms" % max(dt)        
            print "# mean  : %-6.3f ms" % mean
            print "# sigma : %-6.3f ms" % sigma
            print "#"*25
