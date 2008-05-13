
from __future__ import with_statement

import threading
import time
import copy
import sys

from math import sqrt

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

            def doLockedWith (self):

                with self:
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
            case), and as we use 10 threads for the locked case (65
            with lock decorator and 5 with 'with' statement), the
            deviation will be ~ 2.581. We use a simple equals_eps to
            handle load factors that may influence scheduler
            performance and timmings.
            """
            unlocked = []
            locked   = []

            def getObj(o):
                """
                Copy Proxy to share between threads.
                """
                if isinstance(o, Proxy):
                    return copy.copy(o)
                return o

            def runUnlocked():
                unlocked.append(getObj(obj).doUnlocked())

            def runLocked():
                locked.append(getObj(obj).doLocked())

            def runLockedWith():
                locked.append(getObj(obj).doLockedWith())

            threads = []

            print

            for i in range(5):
                t1 = threading.Thread(target=runUnlocked, name="unlocked-%d" % i)
                t2 = threading.Thread(target=runLocked, name="  lock-%d" % i)
                t3 = threading.Thread(target=runLockedWith, name="  with-%d" % i)
                t1.start()
                t2.start()
                t3.start()
                threads += [t1, t2, t3]

            for t in threads:
                t.join()

            unlocked_mean = sum(unlocked)/len(unlocked)
            locked_mean   = sum(locked)/len(locked)

            unlocked_sigma = sqrt(sum([ (unlocked_mean-u)**2 for u in unlocked])/len(unlocked))
            locked_sigma   = sqrt(sum([ (locked_mean-l)**2 for l in locked])/len(locked))

            def equals_eps (a, b, eps=1e-3):
                return abs(a-b) <= eps

            print "unlocked: mean: %.6f sigma: %.6f" % (unlocked_mean, unlocked_sigma)
            print "locked  : mean: %.6f sigma: %.6f" % (locked_mean, locked_sigma)

            assert equals_eps(unlocked_sigma, 0.0, 0.5)
            assert equals_eps(locked_sigma, 2.581, 0.5)


        # direct metaobject
        m = Minimo()
        doTest(m)

        # proxy
        manager = Manager()
        manager.addClass(Minimo, "m", start=True)

        p = manager.getProxy(Minimo)
        doTest(p)

        manager.shutdown()

    def test_lock_config (self):

        class Minimo (ChimeraObject):

            __config__ = {"config": 0}

            def __init__(self):
                ChimeraObject.__init__ (self)

            def doWrite (self):

                for i in range(10):
                    self["config"] = i
                    print "[ write ] - config=%d" % i
                    sys.stdout.flush()
                    time.sleep(0.1)
                    
            def doRead (self):

                for i in range(1000):
                    t0 = time.time()
                    value = self["config"]
                    t = time.time()-t0               
                    print "[  read ] - config=%s took %.6f" % (value, t)
                    sys.stdout.flush()


        m = Minimo()

        t1 = threading.Thread(target=lambda: m.doWrite())
        t2 = threading.Thread(target=lambda: m.doRead())

        print

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        
        
        
        
        





