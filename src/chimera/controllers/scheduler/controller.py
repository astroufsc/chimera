from chimera.core.chimeraobject import ChimeraObject

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.executor import ProgramExecutor

from elixir import session

class Scheduler(ChimeraObject):
    
    __config__ = {"telescope"   : "/Telescope/0",
                  "camera"      : "/Camera/0",
                  "filterwheel" : "/FilterWheel/0",
                  "focuser"     : "/Focuser/0",
                  "dome"        : "/Dome/0",
                  "autofocus"   : "/Autofocus/0",
                  "point_verify": "/PointVerify/0",
                  'site'        : '/Site/0'}
    
    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.machine = Machine(SequentialScheduler(), self)
        self.executor = ProgramExecutor(self)

    def control(self):
        if not self.machine.isAlive():
            self.machine.start()
        else:
            self.machine.state(State.DIRTY)
            return False # that's all folks; control is only run once

    def __start__ (self):
        self.executor.__start__()
        return True
        
    def __stop__ (self):
        self.log.debug('Attempting to stop machine')
        self.machine.state(State.SHUTDOWN)
        self.log.debug('Machine stopped')
        session.commit()
        return True

    def start(self):
        if self.machine:
            self.machine.state(State.DIRTY)


    def pause(self):
        if self.machine:
            self.machine.state(State.PAUSED)

    def stop(self):
        if self.machine:
            self.machine.state(State.SHUTDOWN)

    def state(self):
        return self.machine.state()
        
