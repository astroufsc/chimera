
import threading

class Monitor(threading.Condition):
    """
    Currently, a simple wrapper around a Condition with a Reentrant
    Lock.  Later, more elaborate Monitor, like C# or Java.
    """

    def __init__ (self, lock=None):
        if not lock: lock = threading.RLock()
        threading.Condition.__init__(self, lock)
