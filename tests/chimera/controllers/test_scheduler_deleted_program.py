# SPDX-License-Identifier: GPL-2.0-or-later
"""A program whose row was deleted while it ran must not kill the machine.

The queue is rewritten under running programs as a matter of routine -
robobs cleans it on start AND on stop, plan_robobs rebuilds it - so by the
time the abort lands, the row may be gone. The abort branch logged
`str(task)` after a commit had expired the instance, which reloads the row
and raises ObjectDeletedError from inside an exception handler: the
scheduler-program thread died mid-cleanup, taking the completion event
with it. Seen on opd-40 2026-07-28 on every operator lock during a
program, the abort itself having completed correctly 6 min earlier.
"""

import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chimera.controllers.scheduler import machine as machine_module
from chimera.controllers.scheduler import model
from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import ProgramExecutionAborted

NOW_MJD = 60000.0


def test_str_of_a_deleted_program_does_not_raise(tmp_path):
    """Program.__str__ is used in every scheduler log line, including ones
    inside exception handlers: it must never depend on live database
    state."""
    engine = create_engine(f"sqlite:///{tmp_path / 'scheduler.db'}")
    model.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    session = session_factory()
    program = model.Program(name="WASP-145A", pi="", priority=1)
    session.add(program)
    session.commit()

    # somebody rebuilt the queue while this program was executing
    other = session_factory()
    other.query(model.Program).delete()
    other.commit()

    session.commit()  # expires every instance in the session
    assert str(program).startswith("#")  # must not raise ObjectDeletedError


class FakeSite:
    def mjd(self):
        return NOW_MJD


class Controller:
    def __init__(self):
        self.events = []
        self._config = {"stop_tracking_on_program_end": False, "telescope": None}

    def __getitem__(self, key):
        return self._config[key]

    def get_site(self):
        return FakeSite()

    def program_begin(self, program_id):
        pass

    def program_complete(self, program_id, status, message=None):
        self.events.append((status, message))

    def state_changed(self, new, old):
        pass


class DeletedRowProgram:
    """A program whose row disappears mid-run: formatting it then reloads
    the row, exactly as an expired SQLAlchemy instance does."""

    id = 1
    start_at = 0.0
    valid_for = -1

    def __init__(self):
        self.deleted = False

    def __str__(self):
        if self.deleted:
            raise RuntimeError("Instance <Program> has been deleted")
        return "#1 WASP-145A pi: #actions: 3"


class Scheduler:
    def reschedule(self, machine):
        pass

    def __next__(self):
        return None

    def done(self, task, error=None):
        # SequentialScheduler logs the task it is closing out
        str(task)


class AbortingExecutor:
    """The queue is rewritten, then the abort the operator asked for lands."""

    def __init__(self, program):
        self.program = program

    def __start__(self):
        pass

    def stop(self):
        pass

    def execute(self, program):
        self.program.deleted = True
        raise ProgramExecutionAborted()


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    class FakeSession:
        def merge(self, obj):
            return obj

        def commit(self):
            pass

    monkeypatch.setattr(machine_module, "Session", lambda: FakeSession())


def test_aborting_a_deleted_program_keeps_the_machine_alive():
    program = DeletedRowProgram()
    controller = Controller()
    machine = Machine(Scheduler(), AbortingExecutor(program), controller)

    machine.state(State.BUSY)
    machine._process(program)
    machine._worker.join(10)

    assert not machine._worker.is_alive()
    assert controller.events == [(SchedulerStatus.ABORTED, "Aborted by user.")], (
        "the abort's completion event was lost with the thread"
    )
    assert machine.state() == State.OFF
    assert threading.active_count() >= 1
