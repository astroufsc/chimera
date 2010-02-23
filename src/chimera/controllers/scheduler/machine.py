import chimera.core.log

from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.model import Session
from chimera.controllers.scheduler.status import SchedulerStatus

from chimera.core.exceptions import ProgramExecutionException, ProgramExecutionAborted

import threading
import logging

log = logging.getLogger(__name__)

class Machine(threading.Thread):
    
    __state = None
    __stateLock = threading.Lock()
    __wakeUpCall = threading.Condition()
    
    def __init__(self, scheduler, executor, controller):
        threading.Thread.__init__(self)

        self.scheduler = scheduler
        self.executor = executor
        self.controller = controller

        self.currentProgram = None

        self.setDaemon(False)

    def state(self, state=None):
        self.__stateLock.acquire()
        try:
            if not state: return self.__state
            if state == self.__state: return
            self.controller.stateChanged(state, self.__state)
            log.debug("Changing state, from %s to %s." % (self.__state, state))
            self.__state = state
            self.wakeup()
        finally:
            self.__stateLock.release()

    def run(self):
        log.info("Starting scheduler machine")
        self.state(State.OFF)

        # inject instruments on handlers
        self.executor.__start__()

        while self.state() != State.SHUTDOWN:

            if self.state() == State.OFF:
                log.debug("[off] will just sleep..")
                self.sleep()

            if self.state() == State.START:
                log.debug("[start] database changed, rescheduling...")
                self.scheduler.reschedule(self)
                self.state(State.IDLE)

            if self.state() == State.IDLE:

                log.debug("[idle] looking for something to do...")

                # find something to do
                program = self.scheduler.next()

                if program:
                    log.debug("[idle] there is something to do, processing...")
                    self.state(State.BUSY)
                    self.currentProgram = program
                    self._process(program)
                    continue

                # should'nt get here if any task was executed
                log.debug("[idle] there is nothing to do, going offline...")
                self.currentProgram = None
                self.state(State.OFF)

            elif self.state() == State.BUSY:
                log.debug("[busy] waiting tasks to finish..")
                self.sleep()

            elif self.state() == State.STOP:
                log.debug("[stop] trying to stop current program")
                self.executor.stop()
                self.state(State.OFF)

            elif self.state() == State.SHUTDOWN:
                log.debug("[shutdown] trying to stop current program")
                self.executor.stop()
                log.debug("[shutdown] should die soon.")
                break

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

        def process ():

            # session to be used by executor and handlers
            session = Session()

            task = session.merge(program)

            log.debug("[start] %s" % str(task))

            self.controller.programBegin(program)

            try:
                self.executor.execute(task)
                log.debug("[finish] %s" % str(task)) 
                self.scheduler.done(task)
                self.controller.programComplete(program, SchedulerStatus.OK)
                self.state(State.IDLE)
            except ProgramExecutionException, e:
                self.scheduler.done(task, error=e)
                self.controller.programComplete(program, SchedulerStatus.ERROR, str(e))
                self.state(State.IDLE)
                log.debug("[error] %s (%s)" % (str(task), str(e)))
            except ProgramExecutionAborted, e:
                self.scheduler.done(task, error=e)
                self.controller.programComplete(program, SchedulerStatus.ABORTED, "Aborted by user.")
                self.state(State.OFF)
                log.debug("[aborted by user] %s" % str(task))

            session.commit()

        t = threading.Thread(target=process)
        t.setDaemon(False)
        t.start()
