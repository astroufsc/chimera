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
