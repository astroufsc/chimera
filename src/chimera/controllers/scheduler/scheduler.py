

from chimera.core.chimeraobject import ChimeraObject

from chimera.controllers.scheduler.machine import Machine, State

import threading

__all__ = ['Scheduler']


class Scheduler (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)
        
        self.machine = Machine()

    def control (self):
        self.machine.state(State.DIRTY)
        t = threading.Thread(target=self.machine.run)
        t.setDaemon(False)
        t.start()
        return False # that's al folks

    def __stop__ (self):
        self.machine.state(State.SHUTDOWN)
