
from chimera.util.enum import Enum

from chimera.controllers.scheduler.clock    import Clock
from chimera.controllers.scheduler.sensors  import Sensors
from chimera.controllers.scheduler.schedulers   import *

from chimera.controllers.scheduler.model import *

import chimera.core.log

import logging
import threading

log = logging.getLogger(__name__)


__all__ = ['Machine', 'State']


State = Enum("OFF", "DIRTY", "IDLE", "BUSY", "SHUTDOWN")


class Machine (object):

    __state = None
    __stateLock  = threading.Lock()
    __wakeUpCall = threading.Condition()    

    def __init__ (self):
        
        self.clock = Clock(self)
        self.sensors = Sensors()
        self.scheduler = SequentialScheduler()
        self.state(State.OFF)

    def run (self):

        log.info("Starting scheduler machine")

        while True:

            if self.state() == State.OFF:
                log.debug("[off] will just sleep..")
                pass

            if self.state() == State.DIRTY:
                log.debug("[dirty] database changed, rescheduling...")
                self.scheduler.reschedule(self)
                self.state(State.IDLE)
                continue

            if self.state() == State.IDLE:

                log.debug("[idle] looking for something to do...")

                # find something to do
                exposure = self.scheduler.next(self.clock.now(), self.sensors.sense())

                if exposure:
                    log.debug("[idle] there is something to do, processing...")
                    self.state(State.BUSY)
                    self._process(exposure)
                    continue

                # should'nt get here if any task was executed
                log.debug("[idle] there is nothing to do, sleeping...")

            elif self.state() == State.BUSY:
                log.debug("[busy] waiting tasks to finish..")
                pass

            elif self.state() == State.SHUTDOWN:
                log.debug("[shutdown] bye.")
                break

            # RIP
            self.sleep()

    def state(self, state=None):
        self.__stateLock.acquire()
        try:
            if not state: return self.__state
            log.debug("Chaning state, from %s to %s." % (self.__state, state))
            self.__state = state
            self.wakeup()
        finally:
            self.__stateLock.release()

    def sleep(self):
        self.__wakeUpCall.acquire()
        log.debug("Sleeping")
        self.__wakeUpCall.wait()
        self.__wakeUpCall.release()

    def wakeup(self):
        self.__wakeUpCall.acquire()
        log.debug("Waking up")
        self.__wakeUpCall.notifyAll()
        self.__wakeUpCall.release()

    def _process(self, exp):

        def process ():
            try:
                exp.process()
            finally:
                self.scheduler.done(exp)
                self.state(State.IDLE)
                
        t = threading.Thread(target=process)
        t.setDaemon(False)
        t.start()
