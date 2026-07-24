import logging
from queue import Queue

from sqlalchemy import desc

from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Program, Session

log = logging.getLogger(__name__)


class SequentialScheduler(IScheduler):
    def __init__(self):
        self.run_queue = None
        self.machine = None

    def reschedule(self, machine):
        self.machine = machine
        self.run_queue = Queue(-1)

        session = Session()

        # FIXME: remove noqa
        # start_at orders execution, priority breaks ties: priority alone
        # let a future-timed program hold the machine with the whole night
        # queued behind it. Programs without start_at sort first and keep
        # the old priority order among themselves.
        programs = (
            session.query(Program)
            .order_by(Program.start_at.asc().nullsfirst(), desc(Program.priority))
            .filter(Program.finished == False)  # noqa
            .all()
        )

        if not programs:
            return

        log.debug(f"rescheduling, found {len(list(programs))} runnable programs")

        for program in programs:
            self.run_queue.put(program)

        machine.wake_up()

    def __next__(self):
        session = Session()
        while not self.run_queue.empty():
            program = self.run_queue.get()
            # reschedule() also enqueues the currently RUNNING program (its
            # finished flag is only written at completion), so entries can
            # be stale by the time they are popped: re-check the database
            current = session.get(Program, program.id)
            if current is None or current.finished:
                self.run_queue.task_done()
                continue
            return program

        return None

    def done(self, task, error=None):
        if error:
            log.debug(f"Error processing program {str(task)}.")
            log.exception(error)
        else:
            task.finished = True

        self.run_queue.task_done()
        self.machine.wake_up()
