import logging
import threading

from chimera.controllers.scheduler.model import Program, Session
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import ProgramExecutionAborted, ProgramExecutionException

log = logging.getLogger(__name__)

#: how long the state machine waits for an abort before carrying on. The
#: abort itself keeps running in the background; this only bounds how long
#: the machine is unable to see a new START.
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
        # handle on the thread running the current program, so the IDLE
        # branch can tell whether one is still in flight
        self._worker = None
        # set by STOP/SHUTDOWN to cancel a program that is still waiting
        # for its slew time. Without it the wait was an uninterruptible
        # time.sleep(): a program queued for 07:50 held the machine for
        # 90 minutes and --stop could not touch it, because executor.stop()
        # only aborts the CURRENT action and this one had not started any.
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

        # publish OUTSIDE the lock: a slow event subscriber must not be able
        # to block a concurrent state() call (e.g. stop() racing the worker)
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
                # A program already executing must not be picked again.
                # START overwrites BUSY, so every start() arriving while a
                # program ran sent us back through here, next(scheduler)
                # returned the SAME still-unfinished program and _process
                # forked another thread for it. Seen live: robobs calls
                # start() once per program it queues, and five concurrent
                # autofocus runs plus four concurrent sky flats were racing
                # on one camera.
                if self._worker is not None and self._worker.is_alive():
                    # Wait for it rather than picking another program. POLL,
                    # do not sleep on the condition variable: the worker sets
                    # IDLE from inside its own thread just before exiting, so
                    # the wakeup can arrive before we sleep and be lost - the
                    # machine then parked forever with nothing left to wake
                    # it (seen live 2026-07-22, right after an autofocus
                    # failed and its worker signalled IDLE on the way out).
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
                # Run the abort OFF this thread. It reaches the camera through
                # a proxy, and that request cannot be served until the current
                # exposure and its readout finish - 280 s observed on a QHY600.
                # Doing it inline froze the whole state machine for that long:
                # a chimera-sched --start in the meantime was invisible and the
                # scheduler looked permanently wedged (2026-07-22).
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
                # executor.stop() blocks until the running action gives up -
                # for a camera that is the rest of the exposure plus readout.
                # A START requested in that window (chimera-sched --start)
                # only flips the state variable, because this thread is not
                # reading it; dropping unconditionally to OFF here threw that
                # request away, so the scheduler stayed dead and the CLI
                # looked like it did nothing.
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

        Called inline on the program thread, before program_complete and
        before the machine returns to IDLE. Ordering matters: issued from a
        detached thread instead, the stop blocks on the telescope lock behind
        the *next* program's slew and lands after it, untracking the target
        that program just acquired (seen live 2026-07-21, robobs).
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
                    # wait_time is in the site's (possibly fast-forwarded)
                    # seconds; sleep the equivalent REAL time so a scaled
                    # clock actually compresses the wait instead of sleeping
                    # sim-seconds as wall-seconds.  speedup is 1.0 normally.
                    try:
                        speedup = float(site.time_speedup())
                    except Exception:
                        speedup = 1.0
                    real_wait = wait_time / speedup if speedup > 0 else wait_time
                    log.debug(
                        "[start] Waiting until MJD %f to start slewing",
                        program.start_at,
                    )
                    log.debug(
                        "[start] Will wait %f s (sim) = %f s (real, %gx)",
                        wait_time,
                        real_wait,
                        speedup,
                    )
                    if self._cancel_wait.wait(real_wait):
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
                # the finished flag must be on disk BEFORE the machine is
                # released: the idle picker re-checks it against the
                # database, and the commit at the end of this function
                # raced that check (stale entries then re-ran the program)
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
