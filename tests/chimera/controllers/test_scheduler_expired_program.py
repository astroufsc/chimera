# SPDX-License-Identifier: GPL-2.0-or-later
"""A program past its validity window must be finished without running.

The expired branch reported program_complete(OK, "not valid anymore") and
then fell through to execute the program anyway - a second, contradictory
program_complete at the end, and anything listening to the first one (robobs
advances its queue on it) raced a program that was still running.
"""

import pytest

from chimera.controllers.scheduler import machine as machine_module
from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus

NOW_MJD = 60000.0
ONE_HOUR = 1.0 / 24.0


class FakeSite:
    def mjd(self):
        return NOW_MJD


class Controller:
    def __init__(self):
        self.begun = []
        self.events = []
        self._config = {"site": "/Site/0", "stop_tracking_on_program_end": False}

    def __getitem__(self, key):
        return self._config[key]

    def get_proxy(self, location):
        return FakeSite()

    def program_begin(self, program_id):
        self.begun.append(program_id)

    def program_complete(self, program_id, status, message=None):
        self.events.append((status, message))

    def state_changed(self, new, old):
        pass


class Scheduler:
    def __init__(self):
        self.done_calls = []

    def reschedule(self, machine):
        pass

    def __next__(self):
        return None

    def done(self, task, error=None):
        self.done_calls.append((task, error))


class Executor:
    def __init__(self):
        self.executed = []

    def __start__(self):
        pass

    def stop(self):
        pass

    def execute(self, program):
        self.executed.append(program)


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    """_process only uses the session to merge/commit; keep the DB out."""

    class FakeSession:
        def merge(self, obj):
            return obj

        def commit(self):
            pass

    monkeypatch.setattr(machine_module, "Session", lambda: FakeSession())


def _run(start_at, valid_for):
    controller = Controller()
    scheduler = Scheduler()
    executor = Executor()
    machine = Machine(scheduler, executor, controller)
    program = type("P", (), {"id": 1, "start_at": start_at, "valid_for": valid_for})()

    machine.state(State.BUSY)
    machine._process(program)
    machine._worker.join(10)
    assert not machine._worker.is_alive(), "the program thread never finished"
    return controller, scheduler, executor, machine


def test_expired_program_is_finished_without_running():
    # start_at one hour ago, valid for one minute
    controller, scheduler, executor, machine = _run(NOW_MJD - ONE_HOUR, 60.0)

    assert executor.executed == [], "an expired program was executed"
    assert controller.begun == []
    assert controller.events == [(SchedulerStatus.OK, "Program not valid anymore.")], (
        f"expected a single completion, got {controller.events}"
    )
    assert len(scheduler.done_calls) == 1, "the expired program was not marked done"
    assert machine.state() == State.IDLE, "the machine was not released"


def test_late_program_without_window_still_runs():
    # valid_for < 0 means no expiry: a late start must still execute, once
    controller, scheduler, executor, machine = _run(NOW_MJD - ONE_HOUR, -1.0)

    assert len(executor.executed) == 1
    assert controller.begun == [1]
    assert controller.events == [(SchedulerStatus.OK, None)]


def test_late_program_inside_its_window_still_runs():
    # one hour late, valid for two hours
    controller, scheduler, executor, machine = _run(NOW_MJD - ONE_HOUR, 7200.0)

    assert len(executor.executed) == 1
    assert controller.events == [(SchedulerStatus.OK, None)]
