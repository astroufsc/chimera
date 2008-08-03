import chimera.core.log
import threading
import logging
from chimera.core.chimeraobject import ChimeraObject
from chimera.controllers.scheduler.states import State

log = logging.getLogger(__name__)

class Machine(threading.Thread):
    
    __state = None
    __stateLock = threading.Lock()
    __wakeUpCall = threading.Condition()
    
    def __init__(self, scheduler, controller):
        threading.Thread.__init__(self)
        self.proxies = {}
        self.scheduler = scheduler
        self.controller = controller
        self.__state=(State.OFF)
        self.setDaemon(False)
    
    def state(self, state=None):
        self.__stateLock.acquire()
        try:
            if not state: return self.__state
            log.debug("Chaning state, from %s to %s." % (self.__state, state))
            self.__state = state
            self.wakeup()
        finally:
            self.__stateLock.release()

    def run(self):
        log.info("Starting scheduler machine")
        self.state(State.DIRTY)

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
                exposure = self.scheduler.next()

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
        
    def _process(self, exp):

        log.debug("Starting to process exposure: "+exp.__str__()) 
        def process ():
            try:
                self.controller.process(exp)
                #FIXME: We should only set done with exposure upon some callback from the imagesave routine
                log.debug("Done with exposure: "+exp.__str__()) 
                self.scheduler.done(exp)
            finally:
                self.state(State.IDLE)
                
        t = threading.Thread(target=process)
        t.setDaemon(False)
        t.start()
