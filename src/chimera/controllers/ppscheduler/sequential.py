
from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Session, Program

from sqlalchemy import desc

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

        session = Session()
        programs = session.query(Program).order_by(desc(Program.priority)).filter(Program.finished == False).all()
        
        if not programs:
            return

        log.debug("rescheduling, found %d runnable programs" % len(list(programs)))

        for program in programs:
            self.rq.put(program)

        machine.wakeup()

    def next (self):
        if not self.rq.empty():
            log.debug("bbbbbbbbbbbbbbbbbbbb self.rq %s",self.rq)
            print self.rq
            return self.rq.get()

        return None

    def done (self, task, error=None):

        if error:
            log.debug("Error processing program %s." % str(task))
            log.exception(error)
        else:
            task.finished = True
        
        self.rq.task_done()
        self.machine.wakeup()
