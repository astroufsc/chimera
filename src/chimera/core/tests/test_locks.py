

import threading
import time
import copy

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock          import lock

from chimera.core.manager import Manager
from chimera.core.proxy   import Proxy

from nose.tools import assert_raises


class TestLock (object):

    def test_autolock (self):

        class Minimo (ChimeraObject):

            def __init__(self):
                ChimeraObject.__init__ (self)

                self.t0 = time.time()

            def doUnlocked (self):
                time.sleep(1)
                t = time.time()-self.t0                
                print "[unlocked] - %s - %.3f" % (threading.currentThread().getName(), t)                
                return t

            @lock
            def doLocked (self):
                time.sleep(1)
                t = time.time()-self.t0                
                print "[ locked ] - %s - %.3f" % (threading.currentThread().getName(), t)                
                return t


        def doTest (obj):

            """Rationale: We use 5 threads for each method (locked and
            unlocked). As unlocked methods isn't serialized, they runs
            'at the same instant', while locked methods will be
            serialized and will run only when the previous one
            finishes.  Each method simulate a load (sleep of 1s) and
            then returns the time of completion (with an arbitrary
            zero point to give small numbers). The deviation from the
            mean of unlocked methods termination times should be
            nearly zero, as every methods runs at the same time. For
            locked ones, the termination time will be a linear
            function with the slope equals to the load (sleep in this
            case), and as we use 5 threads, the deviation will be
            nearly 2.0. We use a simple equals_eps to handle load
            factors that may influence scheduler performance and
            timmings.
            """
            unlocked = []
            locked   = []

            def getObj(o):
                p = None
                if isinstance(o, Proxy):
                    p = copy.copy(o)
                else:
                    p = o
                return p
                
            def runUnlocked():
                unlocked.append(getObj(obj).doUnlocked())
                
            def runLocked():
                locked.append(getObj(obj).doLocked())

            threads = []

            for i in range(5):
                t1 = threading.Thread(target=runUnlocked, name="unlocked-%d" % i)
                t2 = threading.Thread(target=runLocked, name="  locked-%d" % i)
                t1.start()
                t2.start()
                threads += [t1, t2]

            for t in threads:
                t.join()

            unlocked_mean = sum(unlocked)/len(unlocked)
            locked_mean = sum(locked)/len(locked)

            unlocked_sigma2 = sum([ (unlocked_mean-u)**2 for u in unlocked])/len(unlocked)
            locked_sigma2 = sum([ (locked_mean-l)**2 for l in locked])/len(locked)

            def equals_eps (a, b, eps=1e-3):
                return abs(a-b) <= eps

            assert equals_eps(unlocked_sigma2, 0.0, 0.4)
            assert equals_eps(locked_sigma2, 2.0, 0.4)


        # direct metaobject
        m = Minimo()
        doTest(m)

        # proxy
        manager = Manager()
        manager.addClass(Minimo, "m", start=True)

        p = manager.getProxy(Minimo)
        doTest(p)

        manager.shutdown()

        

        

