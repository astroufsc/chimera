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
            self.run_queue.put(program)

        machine.wake_up()

    def __next__(self):
        if not self.run_queue.empty():
            return self.run_queue.get()

        return None

    def done(self, task, error=None):

        if error:
            log.debug(f"Error processing program {str(task)}.")
            log.exception(error)
        else:
            task.finished = True

        self.run_queue.task_done()
        self.machine.wake_up()
