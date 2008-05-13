
from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import *

import chimera.core.log
import logging

log = logging.getLogger(__name__)

from threading import Timer
from Queue import Queue


class SequentialScheduler (IScheduler):

    def __init__ (self):
        self.rq = None
        self.machine = None

    def reschedule (self, machine):

        self.machine = machine

        self.rq = Queue(-1)

        programs = Program.query.filter_by(finished=False).all()

        log.debug("rescheduling, found %d programs." % len(programs))

        for program in programs:
            for obs in program.observations:
                for exp in obs.exposures:
                    self.rq.put(exp)

        machine.wakeup()

    def next (self, now, sensors):
        if not self.rq.empty():
            return self.rq.get()

    def done (self, task):
        self.rq.task_done()
        self.machine.wakeup()
