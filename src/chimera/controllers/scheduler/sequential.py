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
        # Execution order: start_at first, priority as the tie-break.
        # Ordering by priority alone starved the night when a program with
        # a FUTURE start_at outranked everything: the machine picked the
        # morning sky flat at 22:00 and waited 10 h on it while the whole
        # night's science sat queued behind (2026-07-22). Programs without
        # a start_at (hand-written queues) sort first and keep the old
        # priority behaviour among themselves.
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
            # reschedule() rebuilds the queue from every unfinished row -
            # including the program RUNNING at that moment, whose finished
            # flag is only written at completion. By the time its entry is
            # popped it may have finished: re-check the row or the night
            # replays it (a focus ran twice back to back, 2026-07-23).
            current = session.query(Program).get(program.id)
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
