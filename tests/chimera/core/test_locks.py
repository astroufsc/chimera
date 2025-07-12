import copy
import sys
import threading
import time
from math import sqrt

import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.core.proxy import Proxy


class TestLock:
    @pytest.mark.slow
    def test_autolock(self, manager):
        class Minimo(ChimeraObject):
            def __init__(self):
                ChimeraObject.__init__(self)

                self.t0 = time.time()

            def do_unlocked(self):
                time.sleep(1)
                t = time.time() - self.t0
                print(f"[unlocked] - {threading.current_thread().name} - {t:.3f}")
                return t

            @lock
            def do_locked(self):
                time.sleep(1)
                t = time.time() - self.t0
                print(f"[ locked ] - {threading.current_thread().name} - {t:.3f}")
                return t

        def do_test(obj):
            """Rationale: We use 5 threads for each method (locked and
            unlocked). As unlocked methods isn't serialized, they run
            'at the same instant', while locked methods will be
            serialized and will run only when the previous one
            finishes.  Each method simulate a load (sleep of 1s) and
            then returns the time of completion (with an arbitrary
            zero point to give small numbers). The deviation from the
            mean of unlocked methods termination times should be
            nearly zero, as every methods runs at the same time. For
            locked ones, the termination time will be a linear
            function with the slope equals to the load (sleep in this
            case), and as we use 10 threads for the locked case, the
            deviation will be ~ 2.872. We use a simple equals_eps to
            handle load factors that may influence scheduler
            performance and timmings.
            """
            unlocked = []
            locked = []

            def get_obj(o):
                """
                Copy Proxy to share between threads.
                """
                if isinstance(o, Proxy):
                    return copy.copy(o)
                return o

            def run_unlocked():
                unlocked.append(get_obj(obj).do_unlocked())

            def run_locked():
                locked.append(get_obj(obj).do_locked())

            threads = []

            print()

            for i in range(10):
                t1 = threading.Thread(target=run_unlocked, name=f"unlocked-{i}")
                t2 = threading.Thread(target=run_locked, name=f"  lock-{i}")

                t1.start()
                t2.start()

                threads += [t1, t2]

            for t in threads:
                t.join()

            unlocked_mean = sum(unlocked) / len(unlocked)
            locked_mean = sum(locked) / len(locked)

            unlocked_sigma = sqrt(
                sum([(unlocked_mean - lock) ** 2 for lock in unlocked]) / len(unlocked)
            )
            locked_sigma = sqrt(
                sum([(locked_mean - lock) ** 2 for lock in locked]) / len(locked)
            )

            def equals_eps(a, b, eps=1e-3):
                return abs(a - b) <= eps

            print(f"unlocked: mean: {unlocked_mean:.6f} sigma: {unlocked_sigma:.6f}")
            print(f"locked  : mean: {locked_mean:.6f} sigma: {locked_sigma:.6f}")

            assert equals_eps(unlocked_sigma, 0.0, 0.5) is True
            assert equals_eps(locked_sigma, 2.875, 1.0) is True

        # direct metaobject
        m = Minimo()
        do_test(m)

        # proxy
        manager.add_class(Minimo, "m", start=True)

        p = manager.get_proxy("/Minimo/m")
        do_test(p)

    def test_lock_config(self):
        class Minimo(ChimeraObject):
            __config__ = {"config": 0}

            def __init__(self):
                ChimeraObject.__init__(self)

            def do_write(self):
                for i in range(10):
                    self["config"] = i
                    print(f"[ write ] - config={i}")
                    sys.stdout.flush()
                    time.sleep(0.1)

            def do_read(self):
                for i in range(1000):
                    t0 = time.time()
                    value = self["config"]
                    t = time.time() - t0
                    print(f"[  read ] - config={value} took {t:.6f}")
                    sys.stdout.flush()

        m = Minimo()

        t1 = threading.Thread(target=lambda: m.do_write())
        t2 = threading.Thread(target=lambda: m.do_read())

        print()

        t1.start()
        t2.start()

        t1.join()
        t2.join()
