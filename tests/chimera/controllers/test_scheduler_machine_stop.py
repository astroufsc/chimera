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
