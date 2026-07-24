import logging
import threading

from chimera.controllers.scheduler.model import Program, Session
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import ProgramExecutionAborted, ProgramExecutionException

log = logging.getLogger(__name__)

#: max time STOP waits for the abort; past it the abort continues in the
#: background and the machine carries on
STOP_ABORT_TIMEOUT = 30.0


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
        # thread running the current program; the IDLE branch waits on it
        self._worker = None
        # set by STOP/SHUTDOWN to release a program still waiting for its
        # slew time (executor.stop() only aborts an action already started)
        self._cancel_wait = threading.Event()

        self.daemon = False

    def state(self, state=None):
        self.__state_lock.acquire()
        try:
            if not state:
                return self.__state
            if state == self.__state:
                return
            old_state = self.__state
            log.debug(f"Changing state, from {old_state} to {state}.")
            self.__state = state
            self.wake_up()
        finally:
            self.__state_lock.release()

        # publish outside the lock: a slow subscriber must not block state()
        self.controller.state_changed(state, old_state)

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
                # START overwrites BUSY, so a start() during a run lands here
                # with the same unfinished program: wait for the worker
                # instead of forking a duplicate execution
                if self._worker is not None and self._worker.is_alive():
                    # poll, don't sleep(): the worker signals IDLE just
                    # before exiting, so the wakeup can be lost
                    self._worker.join(1.0)
                    continue

                log.debug("[idle] looking for something to do...")

                # find something to do
                program = next(self.scheduler)

                if program:
                    log.debug("[idle] there is something to do, processing...")
                    log.debug("[idle] program slew start %s", program.start_at)
                    self.state(State.BUSY)
                    self._cancel_wait.clear()
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
                # release a program still counting down to its slew time
                self._cancel_wait.set()
                # abort off this thread: executor.stop() blocks until the
                # running action yields (a full camera readout), and inline
                # it froze the whole state machine for that long
                stopper = threading.Thread(
                    target=self.executor.stop, name="scheduler-stop", daemon=True
                )
                stopper.start()
                stopper.join(STOP_ABORT_TIMEOUT)
                if stopper.is_alive():
                    log.warning(
                        "[stop] abort still running after %.0f s; carrying on "
                        "(it will finish in the background)",
                        STOP_ABORT_TIMEOUT,
                    )
                # a START requested during the abort only flips the state
                # variable; dropping unconditionally to OFF discarded it
                if self.state() == State.STOP:
                    self.state(State.OFF)

            elif self.state() == State.SHUTDOWN:
                log.debug("[shutdown] trying to stop current program")
                self._cancel_wait.set()
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

    def _stop_tracking(self):
        """Leave the mount idle at the end of a program.

        Must run inline on the program thread, before program_complete:
        from a detached thread the stop queues behind the next program's
        slew and untracks the target it just acquired.
        """
        if not self.controller["stop_tracking_on_program_end"]:
            return

        location = self.controller["telescope"]
        # a string-typed chimera config key coerces None to "None"
        if not location or str(location).lower() in ("none", ""):
            return

        try:
            telescope = self.controller.get_proxy(location)
            if telescope.is_tracking():
                telescope.stop_tracking()
                log.info("Tracking stopped at program end.")
        except Exception:
            # never let this fail the program that just ran
            log.exception("Could not stop telescope tracking at program end.")

    def _process(self, program):
        def process():
            # session to be used by executor and handlers
            session = Session()

            task = session.merge(program)

            log.debug(f"[start] {str(task)}")

            # the configured site, not a private Site(): one clock system-wide
            site = self.controller.get_proxy(self.controller["site"])
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
                    if self._cancel_wait.wait(wait_time):
                        log.debug("[start] wait cancelled; abandoning %s", str(task))
                        self.controller.program_complete(
                            program.id,
                            SchedulerStatus.ABORTED,
                            "Aborted while waiting for its slew time.",
                        )
                        return
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
                "[start] Proceeding since MJD %f should have passed", program.start_at
            )
            self.controller.program_begin(program.id)

            try:
                self.executor.execute(task)
                log.debug(f"[finish] {str(task)}")
                self.scheduler.done(task)
                # commit the finished flag before releasing the machine:
                # the idle picker re-checks it against the database
                session.commit()
                self._stop_tracking()
                self.controller.program_complete(program.id, SchedulerStatus.OK)
                self.state(State.IDLE)
            except ProgramExecutionException as e:
                self.scheduler.done(task, error=e)
                session.commit()
                self._stop_tracking()
                self.controller.program_complete(
                    program.id, SchedulerStatus.ERROR, str(e)
                )
                self.state(State.IDLE)
                log.debug(f"[error] {str(task)} ({str(e)})")
            except ProgramExecutionAborted as e:
                self.scheduler.done(task, error=e)
                session.commit()
                self._stop_tracking()
                self.controller.program_complete(
                    program.id, SchedulerStatus.ABORTED, "Aborted by user."
                )
                self.state(State.OFF)
                log.debug(f"[aborted by user] {str(task)}")

            session.commit()

        t = threading.Thread(target=process, name="scheduler-program")
        t.daemon = False
        self._worker = t
        t.start()
