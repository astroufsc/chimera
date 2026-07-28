import logging
import threading

from chimera.controllers.scheduler.model import Program, Session
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import (
    BusDeadException,
    ObjectNotFoundException,
    ProgramExecutionAborted,
    ProgramExecutionException,
)

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
        self.current_worker = None

        # a hung instrument must not block interpreter exit: the graceful
        # path joins this thread explicitly (Scheduler.__stop__)
        self.daemon = True

    def state(self, state=None):
        self.__state_lock.acquire()
        try:
            if not state:
                return self.__state
            if state == self.__state:
                return
            if self.__state == State.SHUTDOWN:
                # terminal: a finishing worker must not resurrect the machine
                # by setting IDLE/OFF concurrently with shutdown
                log.debug(f"Ignoring change to {state}: machine is shutting down.")
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

        # one state snapshot per iteration: SHUTDOWN is checked first, so a
        # shutdown requested while BUSY still runs executor.stop() (the old
        # while-condition exited the loop right past that branch)
        while True:
            state = self.state()

            if state == State.SHUTDOWN:
                log.debug("[shutdown] trying to stop current program")
                self.executor.stop()
                log.debug("[shutdown] should die soon.")
                break

            if state == State.OFF:
                log.debug("[off] will just sleep..")
                self.sleep(until_leaves=State.OFF)

            elif state == State.START:
                log.debug("[start] database changed, rescheduling...")
                self.scheduler.reschedule(self)
                self.state(State.IDLE)

            elif state == State.IDLE:
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

            elif state == State.BUSY:
                log.debug("[busy] waiting tasks to finish..")
                self.sleep(until_leaves=State.BUSY)

            elif state == State.STOP:
                log.debug("[stop] trying to stop current program")
                self.executor.stop()
                self.state(State.OFF)

        log.debug("[shutdown] thread ending...")

    def sleep(self, until_leaves=None):
        with self.__wake_up_call:
            log.debug("Sleeping")
            if until_leaves is None:
                self.__wake_up_call.wait()
            else:
                # re-check under the condition lock: a state change notified
                # between our caller's snapshot and this wait must not be lost
                self.__wake_up_call.wait_for(lambda: self.__state != until_leaves)

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

            # the events and instrument calls below talk to the bus: keep
            # everything under one try so a dying bus can never kill this
            # thread unhandled
            try:
                # the manager-injected site, not a private Site(): one clock
                # system-wide
                site = self.controller.get_site()
                now_mjd = site.mjd()
                log.debug("[start] Current MJD is %f", now_mjd)
                if program.start_at:
                    wait_time = (program.start_at - now_mjd) * 86.4e3
                    if wait_time > 0.0:
                        log.debug(
                            "[start] Waiting until MJD %f to start slewing",
                            program.start_at,
                        )
                        log.debug("[start] Will wait %f s (site time)", wait_time)
                        # Poll the site clock so a fast-forwarded site compresses
                        # the wait for free (no speedup knowledge here), and block
                        # on the machine's wake-up Condition -- notified on every
                        # state change -- so a STOP/SHUTDOWN breaks the wait at once
                        # instead of after a fixed sleep.
                        while site.mjd() < program.start_at:
                            if self.state() in (State.STOP, State.SHUTDOWN):
                                log.debug(
                                    "[start] Aborted while waiting for slew start"
                                )
                                return
                            with self.__wake_up_call:
                                self.__wake_up_call.wait(1.0)
                    else:
                        if program.valid_for >= 0.0:
                            if -wait_time > program.valid_for:
                                log.debug(
                                    "[start] Program is not valid anymore {program.start_at}, {program.valid_for}"
                                )
                                self.controller.program_complete(
                                    program.id,
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
                    "[start] Proceeding since MJD %f should have passed",
                    program.start_at,
                )
                self.controller.program_begin(program.id)

                self.executor.execute(task)
                log.debug(f"[finish] {str(task)}")
                self.scheduler.done(task)
                self.controller.program_complete(program.id, SchedulerStatus.OK)
                self.state(State.IDLE)
            except ProgramExecutionException as e:
                self.scheduler.done(task, error=e)
                self.controller.program_complete(
                    program.id, SchedulerStatus.ERROR, str(e)
                )
                self.state(State.IDLE)
                log.debug(f"[error] {str(task)} ({str(e)})")
            except ProgramExecutionAborted as e:
                self.scheduler.done(task, error=e)
                self.controller.program_complete(
                    program.id, SchedulerStatus.ABORTED, "Aborted by user."
                )
                self.state(State.OFF)
                log.debug(f"[aborted by user] {str(task)}")
            except BusDeadException as e:
                # the bus died: record an abort, never march on to the
                # next program
                log.warning(f"[aborted] {str(task)}: bus is dead ({e})")
                self.scheduler.done(task, error=e)
                self.controller.program_complete(
                    program.id, SchedulerStatus.ABORTED, "System shutdown."
                )
                self.state(State.OFF)  # ignored when already shutting down
            except ObjectNotFoundException as e:
                if self.state() in (State.STOP, State.SHUTDOWN):
                    # proxies vanish while the system tears down: an abort,
                    # not a program failure
                    log.warning(f"[aborted] {str(task)}: {e}")
                    self.scheduler.done(task, error=e)
                    self.controller.program_complete(
                        program.id, SchedulerStatus.ABORTED, "System shutdown."
                    )
                    self.state(State.OFF)
                else:
                    # the program needs an object that is not deployed: fail
                    # this program, keep the schedule going
                    log.warning(f"[error] {str(task)}: {e}")
                    self.scheduler.done(task, error=e)
                    self.controller.program_complete(
                        program.id, SchedulerStatus.ERROR, str(e)
                    )
                    self.state(State.IDLE)
            finally:
                session.commit()

        # arm here, not in execute(): stop() runs on this same (machine)
        # thread, so an abort can never race the worker to the flag
        self.executor.must_stop.clear()

        t = threading.Thread(target=process, name=f"scheduler-program-{program.id}")
        t.daemon = True
        self.current_worker = t
        t.start()
