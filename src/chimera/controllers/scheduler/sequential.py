
from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Program

from sqlalchemy import desc
from elixir import session

import chimera.core.log
import logging

log = logging.getLogger(__name__)

from Queue import Queue


class SequentialScheduler (IScheduler):

    def __init__ (self):
        self.rq = None
        self.machine = None

    def reschedule (self, machine):

        self.machine = machine
        self.rq = Queue(-1)

        programs = Program.query.order_by(desc(Program.priority)).filter(Program.finished == False)
        
        if not programs:
            return

        log.debug("rescheduling, found %d runnable programs" % len(list(programs)))

        for program in programs:
            self.rq.put(program)

        machine.wakeup()

    def next (self):
        if not self.rq.empty():
            return self.rq.get()

    def done (self, task, error=None):
        # we could not reuse the Program object because we don't know which thread created it
        # and sqlite doesn't like multiple threads touching the same objects.
        program = Program.query.filter_by(id=task.id).one()

        if error:
            log.debug("Error processing program %s." % str(program))
            log.exception(error)
        else:
            program.finished = True
            program.flush()
            session.commit()
        
        self.rq.task_done()
        self.machine.wakeup()
