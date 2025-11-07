import logging
import threading
import time

from chimera.controllers.scheduler.model import Program, Session
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import ProgramExecutionAborted, ProgramExecutionException
from chimera.core.site import Site

log = logging.getLogger(__name__)


class Machine(threading.Thread):
    __state = None
    __state_lock = threading.Lock()
    __wake_up_call = threading.Condition()

    def __init__(self, scheduler, executor, controller):
        threading.Thread.__init__(self)

        self.scheduler = scheduler
        self.executor = executor
        self.controller = controller

        self.current_program = None

        self.daemon = False

    def state(self, state=None):
        self.__state_lock.acquire()
        try:
            if not state:
                return self.__state
            if state == self.__state:
                return
            self.controller.state_changed(state, self.__state)
            log.debug(f"Changing state, from {self.__state} to {state}.")
            self.__state = state
            self.wake_up()
        finally:
            self.__state_lock.release()

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
                program = next(self.scheduler)

                if program:
                    log.debug("[idle] there is something to do, processing...")
                    log.debug("[idle] program slew start %s", program.start_at)
                    self.state(State.BUSY)
                    self.current_program = program
                    self._process(program)
                    continue

                # should'nt get here if any task was executed
                log.debug("[idle] there is nothing to do, going offline...")
                self.current_program = None
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

        log.debug("[shutdown] thread ending...")

    def sleep(self):
        self.__wake_up_call.acquire()
        log.debug("Sleeping")
        self.__wake_up_call.wait()
        self.__wake_up_call.release()

    def wake_up(self):
        self.__wake_up_call.acquire()
        log.debug("Waking up")
        self.__wake_up_call.notify_all()
        self.__wake_up_call.release()

    def restart_all_programs(self):
        session = Session()

        programs = session.query(Program).all()
        for program in programs:
            program.finished = False

        session.commit()

    def _process(self, program):
        def process():
            # session to be used by executor and handlers
            session = Session()

            task = session.merge(program)

            log.debug(f"[start] {str(task)}")

            site = Site()
            now_mjd = site.mjd()
            log.debug("[start] Current MJD is %f", now_mjd)
            if program.start_at:
                wait_time = (program.start_at - now_mjd) * 86.4e3
                if wait_time > 0.0:
                    log.debug(
                        "[start] Waiting until MJD %f to start slewing",
                        program.start_at,
                    )
                    log.debug("[start] Will wait for %f seconds", wait_time)
                    time.sleep(wait_time)
                else:
                    if program.valid_for >= 0.0:
                        if -wait_time > program.valid_for:
                            log.debug(
                                "[start] Program is not valid anymore {program.start_at}, {program.valid_for}"
                            )
                            self.controller.program_complete(
                                program,
                                SchedulerStatus.OK,
                                "Program not valid anymore.",
                            )
                    else:
                        log.debug(
                            "[start] Specified slew start MJD %s has already passed; proceeding without waiting",
                            program.start_at,
                        )
            else:
                log.debug("[start] No slew time specified, so no waiting")
            log.debug("[start] Current MJD is %f", site.mjd())
            log.debug(
                "[start] Proceeding since MJD %f should have passed", program.start_at
            )
            self.controller.program_begin(program)

            try:
                self.executor.execute(task)
                log.debug(f"[finish] {str(task)}")
                self.scheduler.done(task)
                self.controller.program_complete(program, SchedulerStatus.OK)
                self.state(State.IDLE)
            except ProgramExecutionException as e:
                self.scheduler.done(task, error=e)
                self.controller.program_complete(program, SchedulerStatus.ERROR, str(e))
                self.state(State.IDLE)
                log.debug(f"[error] {str(task)} ({str(e)})")
            except ProgramExecutionAborted as e:
                self.scheduler.done(task, error=e)
                self.controller.program_complete(
                    program, SchedulerStatus.ABORTED, "Aborted by user."
                )
                self.state(State.OFF)
                log.debug(f"[aborted by user] {str(task)}")

            session.commit()

        t = threading.Thread(target=process)
        t.daemon = False
        t.start()
