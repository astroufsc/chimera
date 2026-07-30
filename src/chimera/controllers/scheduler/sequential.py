import logging

from sqlalchemy import desc, or_

from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Program, Session

log = logging.getLogger(__name__)

#: Order among programs that are all ready to run RIGHT NOW: priority first,
#: then the earliest start_at, then insertion order - a hand-written
#: `chimera-sched --new` queue runs in the order the targets appear in the
#: YAML, which is what anyone writing that file expects (they used to come
#: out reversed).
_READY_ORDER = (
    desc(Program.priority),
    Program.start_at.asc().nullsfirst(),
    Program.id.asc(),
)

#: Order when nothing is ready yet: whatever becomes ready soonest.
_WAITING_ORDER = (Program.start_at.asc(), desc(Program.priority), Program.id.asc())

#: The static order, used only where there is no clock to judge eligibility
#: with (bare test harnesses).
_STATIC_ORDER = (
    Program.start_at.asc().nullsfirst(),
    desc(Program.priority),
    Program.id.asc(),
)


class SequentialScheduler(IScheduler):
    def __init__(self):
        self.machine = None
        # programs that errored since the last reschedule: skipped by
        # __next__ so a failing program cannot livelock the machine, and
        # retried once the queue is rebuilt (the FIFO this replaced behaved
        # the same way - popped meant not offered again until a reschedule)
        self._deferred = set()

    def reschedule(self, machine):
        self.machine = machine
        self._deferred = set()

        session = Session()
        pending = (
            session.query(Program).filter(Program.finished == False).count()  # noqa
        )
        log.debug(f"rescheduling, found {pending} runnable programs")
        if pending:
            machine.wake_up()

    def _now_mjd(self):
        try:
            return float(self.machine.controller.get_site().mjd())
        except Exception:
            log.exception("No site clock available; using the static time order.")
            return None

    def __next__(self):
        """The highest-priority READY program, else the one ready soonest.

        Selection is by time first, but on ELIGIBILITY rather than a static
        sort: a start_at of 0/None means "no constraint" and one in the past
        means "overdue", and both are ready NOW - so priority ranks them. A
        FUTURE start_at makes a program ineligible until its time comes, so
        a morning flat queued at 22:00 cannot park the machine for 10 h with
        the whole night queued behind it (2026-07-22).

        Sorting statically by start_at instead starved every pinned program
        behind a continuous unpinned one: the sentinel 0.0 reads as
        "earliest", so a monitoring chain that begins a new visit the second
        the last one ends won every pop, even hours past the pinned
        program's start_at - the 00:58 timed focus never ran on opd-40
        2026-07-28 although priority ranked it above the monitor.

        Every call re-queries, so a program that finished while an entry sat
        in a queue cannot be replayed - the FIFO this replaced needed an
        explicit staleness re-check for that.

        Programs that errored since the last reschedule are skipped rather
        than retried forever.
        """
        session = Session()
        pending = session.query(Program).filter(Program.finished == False)  # noqa
        if self._deferred:
            pending = pending.filter(Program.id.notin_(self._deferred))

        now = self._now_mjd()
        if now is None:
            return pending.order_by(*_STATIC_ORDER).first()

        program = (
            pending.filter(
                or_(Program.start_at == None, Program.start_at <= now)  # noqa
            )
            .order_by(*_READY_ORDER)
            .first()
        )

        if program is None:
            # nothing is ready yet: hand over whatever becomes ready first
            # and let the machine wait on its start_at
            program = pending.order_by(*_WAITING_ORDER).first()

        return program

    def done(self, task, error=None):
        if error:
            log.debug(f"Error processing program {str(task)}.")
            log.exception(error)
            self._deferred.add(task.id)
        else:
            task.finished = True

        self.machine.wake_up()
