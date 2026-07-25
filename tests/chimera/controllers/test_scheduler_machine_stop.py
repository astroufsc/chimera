# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""A START requested while executor.stop() runs must not be discarded.

executor.stop() blocks until the running action gives up; a START in that
window only sets the state variable, and dropping unconditionally to OFF
afterwards threw the request away.
"""

import threading

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State


class Controller:
    def state_changed(self, new, old):
        pass


class Scheduler:
    """Records that the machine acted on a START."""

    def __init__(self):
        self.rescheduled = threading.Event()

    def reschedule(self, machine):
        self.rescheduled.set()

    def __next__(self):
        return None


class Executor:
    """stop() takes time, and an operator asks for a START while it runs."""

    def __init__(self):
        self.machine = None
        self.stopped = threading.Event()

    def __start__(self):
        pass

    def stop(self):
        self.stopped.set()
        self.machine.state(State.START)


def test_start_requested_during_stop_is_honoured():
    executor = Executor()
    scheduler = Scheduler()
    machine = Machine(scheduler, executor, Controller())
    executor.machine = machine
    machine.daemon = True

    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()

    # let it settle into OFF, then ask it to stop the running program
    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)
    machine.state(State.STOP)

    assert executor.stopped.wait(10), "executor.stop() was never called"
    assert scheduler.rescheduled.wait(10), (
        "the START requested during executor.stop() was discarded"
    )

    machine.state(State.SHUTDOWN)
    thread.join(timeout=10)


class PlainScheduler:
    def reschedule(self, machine):
        pass

    def __next__(self):
        return None


class PlainExecutor:
    def __start__(self):
        pass

    def stop(self):
        pass


def test_off_waits_for_the_worker_to_die():
    """STOP must not report OFF while the program thread is alive.

    On opd-40 the machine declared OFF while an exposure loop survived for
    52 minutes behind a closed dome: OFF is only honest once the worker is
    dead, and the machine says STOPPING until then.
    """
    release = threading.Event()
    machine = Machine(PlainScheduler(), PlainExecutor(), Controller())
    machine.daemon = True

    worker = threading.Thread(target=lambda: release.wait(30), daemon=True)
    machine._worker = worker
    worker.start()

    thread = threading.Thread(target=machine.run, daemon=True)
    thread.start()
    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)

    machine.state(State.STOP)

    # while the worker lives the machine must hold STOPPING, never OFF
    threading.Event().wait(1.0)
    assert worker.is_alive()
    assert machine.state() == State.STOPPING

    release.set()
    for _ in range(100):
        if machine.state() == State.OFF:
            break
        threading.Event().wait(0.05)
    assert machine.state() == State.OFF

    machine.state(State.SHUTDOWN)
    thread.join(timeout=10)


def test_worker_completion_cannot_rearm_a_stopped_machine():
    """A program's own completion or error must not re-arm a stopped machine.

    On opd-40 the surviving program eventually died with an error and its
    completion path flipped the stopped machine OFF -> IDLE, re-arming the
    night. Terminal transitions are conditional on BUSY.
    """
    machine = Machine(PlainScheduler(), PlainExecutor(), Controller())

    machine.state(State.STOPPING)
    assert machine.transition(State.BUSY, State.IDLE) is False
    assert machine.state() == State.STOPPING

    machine.state(State.BUSY)
    assert machine.transition(State.BUSY, State.IDLE) is True
    assert machine.state() == State.IDLE
