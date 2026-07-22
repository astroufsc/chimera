# SPDX-License-Identifier: GPL-2.0-or-later
"""The scheduler leaves the mount idle when a program ends, however it ended.

This used to live in robobs, which stopped tracking from a detached thread on
program_complete. is_tracking() is unlocked but stop_tracking() is not, so the
thread sailed past the check and then blocked on the telescope lock behind the
*next* program's slew - landing after it, on a target that had just been
acquired. TheSkyX turns tracking on at the end of an RA/Dec slew, so the stale
stop silently untracked the new target and the dome dropped its lookup table.

Live on 2026-07-21 (opd-40): program #2 finished at 23:18:38.66, the next
program's 47.6 s slew held the lock, and "Tracking stopped" landed at
23:19:25.843 - during the following program's autofocus.

The fix is ordering, not timing: the stop runs inline on the program thread,
before program_complete and while the machine is still BUSY. These tests give
stop_tracking a delay standing in for that lock wait, so a stop moved back onto
its own thread loses the race and fails them.
"""

import threading
import time

import pytest

from chimera.controllers.scheduler import machine as machine_module
from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import ProgramExecutionAborted, ProgramExecutionException

#: stands in for the telescope lock held by the next program's slew (47.6 s
#: live). Long enough that a detached stop lands after program_complete.
LOCK_WAIT = 0.2


class FakeTelescope:
    """Records into the shared timeline so ordering can be asserted."""

    def __init__(self, timeline, tracking=True, delay=LOCK_WAIT):
        self.timeline = timeline
        self.tracking = tracking
        self.delay = delay
        self.calls = []

    def is_tracking(self):
        self.calls.append("is_tracking")
        return self.tracking

    def stop_tracking(self):
        time.sleep(self.delay)  # the lock wait
        self.calls.append("stop_tracking")
        self.timeline.append("stop_tracking")
        self.tracking = False


class FakeSite:
    def mjd(self):
        return 60000.0

    def time_speedup(self):
        return 1.0


class Controller:
    """Stands in for the Scheduler ChimeraObject."""

    def __init__(self, timeline, telescope, stop_tracking=True):
        self.timeline = timeline
        self.telescope = telescope
        self.events = []
        self._config = {
            "site": "/Site/0",
            "telescope": "/Telescope/0",
            "stop_tracking_on_program_end": stop_tracking,
        }

    def __getitem__(self, key):
        return self._config[key]

    def get_proxy(self, location):
        return FakeSite() if location == "/Site/0" else self.telescope

    def program_begin(self, program_id):
        pass

    def program_complete(self, program_id, status, message=None):
        self.events.append(status)
        self.timeline.append("program_complete")

    def state_changed(self, new, old):
        pass


class Scheduler:
    def reschedule(self, machine):
        pass

    def __next__(self):
        return None

    def done(self, task, error=None):
        pass


class Executor:
    """Ends the program the way the test asks for."""

    def __init__(self, raises=None):
        self.raises = raises

    def __start__(self):
        pass

    def stop(self):
        pass

    def execute(self, program):
        if self.raises:
            raise self.raises


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    """_process only uses the session to merge/commit; keep the DB out."""

    class FakeSession:
        def merge(self, obj):
            return obj

        def commit(self):
            pass

    monkeypatch.setattr(machine_module, "Session", lambda: FakeSession())


def _build(telescope_factory, stop_tracking=True, raises=None):
    timeline = []
    telescope = telescope_factory(timeline)
    controller = Controller(timeline, telescope, stop_tracking=stop_tracking)
    machine = Machine(Scheduler(), Executor(raises=raises), controller)
    return timeline, telescope, controller, machine


def _run(machine):
    program = type("P", (), {"id": 1, "start_at": 0.0, "valid_for": -1.0})()
    machine.state(State.BUSY)
    machine._process(program)
    machine._worker.join(10)
    assert not machine._worker.is_alive(), "the program thread never finished"


@pytest.mark.parametrize(
    "raises,expected_status",
    [
        (None, SchedulerStatus.OK),
        (ProgramExecutionException("boom"), SchedulerStatus.ERROR),
        (ProgramExecutionAborted(), SchedulerStatus.ABORTED),
    ],
    ids=["completed", "errored", "aborted"],
)
def test_tracking_stops_before_the_program_is_reported_done(raises, expected_status):
    """However the program ended, the stop must precede program_complete.

    program_complete is what releases the next program: robobs reschedules on
    it, and the machine leaves BUSY right after. A stop issued any later is
    the race this replaced.
    """
    timeline, telescope, controller, machine = _build(FakeTelescope, raises=raises)

    _run(machine)

    assert telescope.calls == ["is_tracking", "stop_tracking"]
    assert controller.events == [expected_status]
    assert timeline == ["stop_tracking", "program_complete"], (
        f"tracking was stopped out of order: {timeline}"
    )


def test_the_stop_happens_while_the_machine_is_still_busy():
    """The ordering that actually prevents the race.

    While the machine is BUSY the IDLE branch cannot pick another program, so
    no slew can be in flight competing for the telescope lock.
    """
    seen_state = []
    holder = []

    class WatchingTelescope(FakeTelescope):
        def stop_tracking(self):
            super().stop_tracking()
            seen_state.append(holder[0].state())

    timeline, telescope, controller, machine = _build(WatchingTelescope)
    holder.append(machine)

    _run(machine)

    assert seen_state == [State.BUSY], (
        f"tracking was stopped in state {seen_state}, not BUSY: the next "
        f"program could already have been picked"
    )


def test_the_stop_is_inline_not_detached():
    """A detached stop is what made it land late; it must be done on return."""
    timeline, telescope, controller, machine = _build(FakeTelescope)
    before = threading.active_count()

    _run(machine)

    # commanded by the time the program thread has finished, with no helper
    # thread left behind to deliver it later
    assert telescope.calls == ["is_tracking", "stop_tracking"]
    assert threading.active_count() <= before


def test_option_off_leaves_tracking_alone():
    timeline, telescope, controller, machine = _build(
        FakeTelescope, stop_tracking=False
    )

    _run(machine)

    assert telescope.calls == []
    assert timeline == ["program_complete"]


def test_a_mount_that_is_not_tracking_is_not_commanded():
    timeline, telescope, controller, machine = _build(
        lambda tl: FakeTelescope(tl, tracking=False)
    )

    _run(machine)

    assert telescope.calls == ["is_tracking"]


def test_a_failing_telescope_does_not_break_the_program():
    """Best effort: the program still has to be reported complete."""

    class BrokenTelescope(FakeTelescope):
        def is_tracking(self):
            raise RuntimeError("no link to the mount")

    timeline, telescope, controller, machine = _build(BrokenTelescope)

    _run(machine)

    assert controller.events == [SchedulerStatus.OK]
