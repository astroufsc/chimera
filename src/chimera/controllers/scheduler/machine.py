import chimera.core.log

from chimera.controllers.scheduler.states import State
from chimera.core.exceptions import ProgramExecutionException

import threading
import logging

log = logging.getLogger(__name__)

class Machine(threading.Thread):
    
    __state = None
    __stateLock = threading.Lock()
    __wakeUpCall = threading.Condition()
    
    def __init__(self, scheduler, controller):
        threading.Thread.__init__(self)

        self.scheduler = scheduler
        self.controller = controller
        self.setDaemon(False)

        self.state(State.OFF)
    
    def state(self, state=None):
        self.__stateLock.acquire()
        try:
            if not state: return self.__state
            log.debug("Changing state, from %s to %s." % (self.__state, state))
            self.__state = state
            self.wakeup()
        finally:
            self.__stateLock.release()

    def run(self):
        log.info("Starting scheduler machine")
        self.state(State.PAUSED)

        while self.state() != State.SHUTDOWN:

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
                program = self.scheduler.next()

                if program:
                    log.debug("[idle] there is something to do, processing...")
                    self.state(State.BUSY)
                    self._process(program)
                    continue

                # should'nt get here if any task was executed
                log.debug("[idle] there is nothing to do, sleeping...")

            elif self.state() == State.BUSY:
                log.debug("[busy] waiting tasks to finish..")
                pass

            elif self.state() == State.PAUSED:
                log.debug("[paused] waiting for someone to make me idle or dirty")

            elif self.state() == State.SHUTDOWN:
                log.debug("[shutdown] should die soon.")
                break

            # Rest In Pieces/Let Sleeping Dogs Lie
            self.sleep()
        
        log.debug('[shutdown] thread ending...')

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
        
    def _process(self, program):

        log.debug("Starting to process program: %s" % str(program)) 
        def process ():
            try:
                self.controller.executor.execute(program)
                log.debug("Done with program: %s" % str(program)) 
                self.scheduler.done(program)
            except ProgramExecutionException, e:
                self.scheduler.done(program, error=e)
            finally:
                self.state(State.IDLE)
                
        t = threading.Thread(target=process)
        t.setDaemon(False)
        t.start()
