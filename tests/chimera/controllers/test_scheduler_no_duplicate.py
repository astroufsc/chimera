# SPDX-License-Identifier: GPL-2.0-or-later
"""A start() arriving while a program runs must not fork a second execution.

robobs calls scheduler.start() once per program it queues. START overwrites
BUSY, so the machine re-entered IDLE, next(scheduler) handed back the SAME
still-unfinished program and _process forked another thread for it - five
concurrent autofocus runs and four concurrent sky flats on one camera.
"""

import threading

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State


class Controller:
    def state_changed(self, new, old):
        pass


class Scheduler:
    """Always offers the same program, as a real queue does until it finishes."""

    def __init__(self, program):
        self.program = program

    def reschedule(self, machine):
        pass

    def __next__(self):
        return self.program


class Executor:
    def __start__(self):
        pass

    def stop(self):
        pass


def test_start_while_busy_does_not_duplicate(monkeypatch):
    started = []
    release = threading.Event()

    program = type("P", (), {"id": 1, "start_at": None})()
    machine = Machine(Scheduler(program), Executor(), Controller())
    machine.daemon = True

    def fake_process(prog):
        started.append(prog)
        t = threading.Thread(target=lambda: release.wait(10), daemon=True)
        machine._worker = t
        t.start()

    monkeypatch.setattr(machine, "_process", fake_process)

    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()

    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)

    machine.state(State.START)  # first ingestion
    for _ in range(100):
        if started:
            break
        threading.Event().wait(0.05)
    assert len(started) == 1

    for _ in range(5):  # robobs queues more
        machine.state(State.START)
        threading.Event().wait(0.1)

    assert len(started) == 1, f"program forked {len(started)} concurrent executions"

    release.set()
    machine.state(State.SHUTDOWN)


def test_machine_recovers_when_the_worker_exits():
    """The worker signals IDLE from inside itself, just before exiting.

    The first version of the duplicate guard answered that by flipping to
    BUSY and sleeping on the condition variable - but the wakeup had
    already been delivered, so nothing woke the machine again and it parked
    forever. Live on 2026-07-22: an autofocus failed, its worker set IDLE on
    the way out, and chimera-sched --start did nothing thereafter.
    """
    picked = []
    program = type("P", (), {"id": 1, "start_at": None})()

    class OneShotScheduler:
        def reschedule(self, machine):
            pass

        def __next__(self):
            return program if len(picked) < 2 else None

    machine = Machine(OneShotScheduler(), Executor(), Controller())
    machine.daemon = True

    def fake_process(prog):
        picked.append(prog)

        def body():
            # signal IDLE from inside the worker, as the real one does, and
            # stay alive a moment longer - that window is the race: the
            # machine sees IDLE while this thread is still running
            machine.state(State.IDLE)
            threading.Event().wait(0.4)

        t = threading.Thread(target=body, daemon=True)
        machine._worker = t
        t.start()

    machine._process = fake_process

    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()

    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)
    machine.state(State.START)

    # the machine must go on to pick the SECOND program, not park
    for _ in range(120):
        if len(picked) >= 2:
            break
        threading.Event().wait(0.05)

    assert len(picked) >= 2, "machine parked after the worker exited"
    machine.state(State.SHUTDOWN)


def test_start_survives_a_slow_abort(monkeypatch):
    """A --start must be acted on even while executor.stop() is still running.

    stop() reaches the camera through a proxy, which cannot be served until
    the exposure and its readout finish - 280 s on a QHY600. Run inline it
    froze the machine for that long and chimera-sched --start did nothing
    (2026-07-22: --new, --stop, --new left the scheduler wedged).
    """
    from chimera.controllers.scheduler import machine as machine_module

    monkeypatch.setattr(machine_module, "STOP_ABORT_TIMEOUT", 0.3)

    rescheduled = threading.Event()
    releasing = threading.Event()

    class SlowExecutor:
        def __start__(self):
            pass

        def stop(self):
            releasing.wait(30)  # the camera readout

    class Scheduler:
        def reschedule(self, machine):
            rescheduled.set()

        def __next__(self):
            return None

    machine = Machine(Scheduler(), SlowExecutor(), Controller())
    machine.daemon = True
    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()

    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)

    machine.state(State.STOP)
    threading.Event().wait(0.1)
    machine.state(State.START)  # operator asks while the abort blocks

    assert rescheduled.wait(5), "the START was not acted on during the abort"

    releasing.set()
    machine.state(State.SHUTDOWN)


def test_stop_cancels_a_program_waiting_for_its_slew_time():
    """--stop must release a program that is only counting down.

    executor.stop() aborts the CURRENT action, but a program queued for a
    future slew_at has not started any: it sat in an uninterruptible
    time.sleep(). On 2026-07-22 a focus queued for 07:50 held the machine
    for 90 minutes, and a freshly loaded queue could not run because the
    IDLE guard was waiting on that same worker.
    """
    machine = Machine(
        type(
            "S", (), {"reschedule": lambda self, m: None, "__next__": lambda self: None}
        )(),
        Executor(),
        Controller(),
    )

    finished = threading.Event()

    def waiter():
        # what _process does while counting down to slew_at
        if machine._cancel_wait.wait(60):
            finished.set()

    machine._worker = threading.Thread(target=waiter, daemon=True)
    machine._worker.start()
    threading.Event().wait(0.1)
    assert machine._worker.is_alive()

    # run() sets OFF as its very first action, so the machine has to be up
    # before STOP is requested or it is simply overwritten
    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()
    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)

    machine.state(State.STOP)

    assert finished.wait(10), "the waiting program was not released by STOP"
    machine.state(State.SHUTDOWN)


def test_sequential_runs_in_time_order():
    """A queue with baked start times must execute chronologically.

    Priority-only ordering starved the night: the morning sky flat
    (highest priority, start_at 08:20 next day) was picked at 22:00 and
    the machine waited 10 h on it with the whole night queued behind
    (2026-07-22). start_at orders execution; priority only breaks ties.
    """
    from chimera.controllers.scheduler.model import Program, Session
    from chimera.controllers.scheduler.sequential import SequentialScheduler

    session = Session()
    session.query(Program).delete()
    session.add(Program(name="morning-flat", priority=0, start_at=61244.35))
    session.add(Program(name="science", priority=-21, start_at=61243.93))
    session.add(Program(name="evening-flat", priority=0, start_at=61243.86))
    session.commit()

    scheduler = SequentialScheduler()
    scheduler.reschedule(type("M", (), {"wake_up": staticmethod(lambda: None)})())

    order = []
    while True:
        program = next(scheduler)
        if program is None:
            break
        order.append(program.name)
    assert order == ["evening-flat", "science", "morning-flat"], order

    session.query(Program).delete()
    session.commit()


def test_finished_program_is_not_rerun_after_reschedule():
    """A reschedule while a program runs re-enqueues that same program (its
    finished flag is only written at completion), and the pop must skip the
    stale entry - or the night replays it. Live on 2026-07-23 02:21: robobs
    handed over the queue one program at a time, each hand-over rebuilt the
    run queue while the first focus was executing, and SAO 189035 ran twice
    back to back."""
    from chimera.controllers.scheduler.model import Program, Session
    from chimera.controllers.scheduler.sequential import SequentialScheduler

    session = Session()
    session.query(Program).delete()
    session.add(Program(name="focus", priority=-2, start_at=61244.19))
    session.add(Program(name="science", priority=-19, start_at=61244.20))
    session.commit()

    machine = type("M", (), {"wake_up": staticmethod(lambda: None)})()
    scheduler = SequentialScheduler()
    scheduler.reschedule(machine)
    running = next(scheduler)
    assert running.name == "focus"

    # robobs hands over another program mid-run: the rebuilt queue holds
    # the still-unfinished focus again
    scheduler.reschedule(machine)

    # the focus completes, exactly as machine._process does it
    worker_session = Session()
    task = worker_session.merge(running)
    scheduler.done(task)
    worker_session.commit()

    picked = next(scheduler)
    assert picked is not None, "the science program was lost with the stale entry"
    assert picked.name == "science", f"finished program re-ran: {picked.name}"

    session = Session()
    session.query(Program).delete()
    session.commit()
