
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.model import Session, Program

import logging

log = logging.getLogger(__name__)


class CircularScheduler (SequentialScheduler):

    def __init__ (self):
        SequentialScheduler.__init__(self)

    def __next__ (self):
        if self.rq.empty():
            session = Session()
            programs = session.query(Program).all()

            for program in programs:
                program.finished = False

            session.commit()
            session.close()

            self.reschedule(self.machine)

        if not self.rq.empty():
            return self.rq.get()

        return None

