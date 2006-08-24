import logging
import time

from uts.core.threads import getThreadPool

class AsyncResult(object):

    def __init__(self, func, pool = None):

        self.func = func
        self.result = None
        self.userCallback = False

        self.waiting = False
        self.sleepTime = 0.1

        self.pool = pool or getThreadPool(10)

    def __call__(self, *args, **kwargs):
        logging.debug("calling synchronously %s with %s %s" % (self.func,
                                                               args, kwargs))

        if(hasattr(self.func, "lock")):
            self.func.lock.acquire()
            
        result = self.func(*args, **kwargs)

        if(hasattr(self.func, "lock")):
            self.func.lock.release()

        return result

    def begin(self, *args, **kwargs):
        logging.debug("calling asynchronously %s with %s %s" % (self.func,
                                                                args, kwargs))

        if(not self.pool):
            logging.error("Cannot run async calls, pool is not seted")
            return False

        self.userCallback = kwargs.pop('callback', None)
        self.waiting = True

        self.pool.queueTask(self.func, args, kwargs, self.resultCallback)

        return self

    def end(self):
        while (self.waiting):
            #wait
            time.sleep(self.sleepTime)

        return self.result

    def resultCallback(self, result):
        self.result = result
        self.waiting = False

        if(self.userCallback):
            self.userCallback(self.result)

