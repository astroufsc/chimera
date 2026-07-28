import threading
import time
import types
from unittest.mock import MagicMock

import pytest

import chimera.controllers.scheduler.machine as machine_module
from chimera.controllers.scheduler.executor import ProgramExecutor
from chimera.controllers.scheduler.handlers import ExposeHandler
from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import (
    BusDeadException,
    ObjectNotFoundException,
    ProgramExecutionAborted,
    ProgramExecutionException,
)


class FakeProgram:
    def __init__(self, program_id=1):
        self.id = program_id
        self.start_at = 0.0
        self.valid_for = -1

    def __str__(self):
        return f"#{self.id} fake program"


class FakeScheduler:
    def __init__(self, programs):
        self._programs = list(programs)
        self.done_calls = []

    def reschedule(self, machine):
        pass

    def __next__(self):
        return self._programs.pop(0) if self._programs else None

    def done(self, task, error=None):
        self.done_calls.append((task, error))


class FakeExecutor:
    """Blocks in execute() until an abort arrives, like a long exposure."""

    def __init__(self):
        self.must_stop = threading.Event()
        self.execute_entered = threading.Event()
        self.stop_calls = 0

    def __start__(self):
        pass

    def execute(self, task):
        self.execute_entered.set()
        if not self.must_stop.wait(5):
            raise AssertionError("abort never arrived")
        raise ProgramExecutionAborted()

    def stop(self):
        self.stop_calls += 1
        self.must_stop.set()


def _wait_for_state(machine, state, timeout=5):
    deadline = time.monotonic() + timeout
    while machine.state() != state and time.monotonic() < deadline:
        time.sleep(0.01)
    assert machine.state() == state, f"machine never reached {state}"


@pytest.fixture
def no_db(monkeypatch):
    # the worker opens a model Session only to merge/commit the program;
    # the machine logic under test never needs the real sqlite file
    session = MagicMock()
    session.merge.side_effect = lambda program: program
    monkeypatch.setattr(machine_module, "Session", MagicMock(return_value=session))


def test_shutdown_while_busy_runs_executor_stop(no_db):
    # regression: SHUTDOWN set while the machine slept in BUSY used to exit
    # the run loop without ever calling executor.stop()
    program = FakeProgram()
    scheduler = FakeScheduler([program])
    executor = FakeExecutor()
    controller = MagicMock()
    controller.get_site.return_value.mjd.return_value = 0.0

    machine = Machine(scheduler, executor, controller)
    machine.start()
    _wait_for_state(machine, State.OFF)  # run() sets OFF on entry
    machine.state(State.START)  # what Scheduler.start() does
    try:
        assert executor.execute_entered.wait(5), "worker never reached execute()"
        assert machine.state() == State.BUSY

        # what Scheduler.__stop__ does
        machine.state(State.SHUTDOWN)
        machine.join(5)
        assert not machine.is_alive(), "machine thread did not exit on SHUTDOWN"
        assert executor.stop_calls == 1

        worker = machine.current_worker
        worker.join(5)
        assert not worker.is_alive(), "program worker did not finish"

        statuses = [c.args[1] for c in controller.program_complete.call_args_list]
        assert statuses == [SchedulerStatus.ABORTED]
        assert isinstance(scheduler.done_calls[0][1], ProgramExecutionAborted)
    finally:
        machine.state(State.SHUTDOWN)
        machine.join(5)


def test_shutdown_state_is_sticky():
    controller = MagicMock()
    machine = Machine(FakeScheduler([]), FakeExecutor(), controller)

    machine.state(State.SHUTDOWN)
    assert controller.state_changed.call_count == 1

    machine.state(State.IDLE)
    machine.state(State.OFF)

    assert machine.state() == State.SHUTDOWN
    assert controller.state_changed.call_count == 1


def test_missing_object_is_program_error(no_db, monkeypatch):
    # a program that needs an undeployed object (e.g. an autofocus action
    # with no Autofocus controller) must not kill the worker thread:
    # outside shutdown it is a program ERROR and the schedule keeps going
    caught = []
    monkeypatch.setattr(threading, "excepthook", lambda args: caught.append(args))

    program = FakeProgram()
    scheduler = FakeScheduler([program])
    executor = FakeExecutor()
    executor.execute = MagicMock(
        side_effect=ObjectNotFoundException("no /Autofocus/0")
    )
    controller = MagicMock()
    controller.get_site.return_value.mjd.return_value = 0.0

    machine = Machine(scheduler, executor, controller)
    machine.start()
    _wait_for_state(machine, State.OFF)  # run() sets OFF on entry
    machine.state(State.START)  # what Scheduler.start() does
    try:
        deadline = time.monotonic() + 5
        while not scheduler.done_calls and time.monotonic() < deadline:
            time.sleep(0.01)
        assert scheduler.done_calls, "worker never reported done()"
        assert isinstance(scheduler.done_calls[0][1], ObjectNotFoundException)

        machine.current_worker.join(5)
        statuses = [c.args[1] for c in controller.program_complete.call_args_list]
        assert statuses == [SchedulerStatus.ERROR]
        # the machine went back to look for the next program (queue is empty)
        _wait_for_state(machine, State.OFF)
        assert not caught, f"worker thread died unhandled: {caught}"
    finally:
        machine.state(State.SHUTDOWN)
        machine.join(5)


def test_worker_aborts_on_dead_bus(no_db):
    # a dead bus must abort the current program and stop the schedule: the
    # old code recorded a generic error and marched on to the next program
    programs = [FakeProgram(1), FakeProgram(2)]
    scheduler = FakeScheduler(programs)
    executor = FakeExecutor()
    executor.execute = MagicMock(side_effect=BusDeadException("bus died"))
    controller = MagicMock()
    controller.get_site.return_value.mjd.return_value = 0.0

    machine = Machine(scheduler, executor, controller)
    machine.start()
    _wait_for_state(machine, State.OFF)  # run() sets OFF on entry
    machine.state(State.START)  # what Scheduler.start() does
    try:
        deadline = time.monotonic() + 5
        while not scheduler.done_calls and time.monotonic() < deadline:
            time.sleep(0.01)
        assert scheduler.done_calls, "worker never reported done()"
        assert isinstance(scheduler.done_calls[0][1], BusDeadException)

        machine.current_worker.join(5)
        _wait_for_state(machine, State.OFF)
        statuses = [c.args[1] for c in controller.program_complete.call_args_list]
        assert statuses == [SchedulerStatus.ABORTED]
        assert executor.execute.call_count == 1, "second program ran on a dead bus"
    finally:
        machine.state(State.SHUTDOWN)
        machine.join(5)


def test_executor_stop_arms_without_handler():
    executor = ProgramExecutor(MagicMock())
    assert executor.current_handler is None

    executor.stop()

    assert executor.must_stop.is_set()


def _expose_action():
    return types.SimpleNamespace(
        filter=None,
        frames=1,
        exptime=1.0,
        shutter="OPEN",
        image_type="OBJECT",
        filename="test",
        object_name="obj",
        window=None,
        binning=None,
        wait_dome=False,
        compress_format="NO",
        program=types.SimpleNamespace(name="PRG", pi="pi"),
    )


@pytest.fixture
def expose_instruments():
    ExposeHandler.camera = MagicMock()
    ExposeHandler.filterwheel = MagicMock()
    yield ExposeHandler.camera
    del ExposeHandler.camera
    del ExposeHandler.filterwheel


def test_expose_handler_reraises_bus_death(expose_instruments):
    expose_instruments.expose.side_effect = BusDeadException("bus died")

    with pytest.raises(BusDeadException):
        ExposeHandler.process(_expose_action())


def test_expose_handler_wraps_ordinary_errors(expose_instruments):
    expose_instruments.expose.side_effect = RuntimeError("boom")

    with pytest.raises(ProgramExecutionException):
        ExposeHandler.process(_expose_action())
