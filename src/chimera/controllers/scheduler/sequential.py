from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Session, Program

from sqlalchemy import desc

from queue import Queue

import logging

log = logging.getLogger(__name__)


class SequentialScheduler(IScheduler):

    def __init__(self):
        self.rq = None
        self.machine = None

    def reschedule(self, machine):

        self.machine = machine
        self.rq = Queue(-1)

        session = Session()

        # FIXME: remove noqa
        programs = (
            session.query(Program)
            .order_by(desc(Program.priority))
            .filter(Program.finished == False)  # noqa
            .all()
        )

        if not programs:
            return

        log.debug(f"rescheduling, found {len(list(programs))} runnable programs")

        for program in programs:
            self.rq.put(program)

        machine.wakeup()

    def __next__(self):
        if not self.rq.empty():
            return self.rq.get()

        return None

    def done(self, task, error=None):

        if error:
            log.debug(f"Error processing program {str(task)}.")
            log.exception(error)
        else:
            task.finished = True

        self.rq.task_done()
        self.machine.wakeup()
