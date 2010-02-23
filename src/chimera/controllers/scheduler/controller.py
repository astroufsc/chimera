from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.executor import ProgramExecutor
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.model import Session

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
        
        self.executor = ProgramExecutor(self)
        self.scheduler = SequentialScheduler()

        self.machine = Machine(self.scheduler, self.executor, self)

    def control(self):
        if not self.machine.isAlive():
            self.machine.start()
            return False

    def __stop__ (self):
        self.log.debug('Attempting to stop machine')
        self.shutdown()
        self.log.debug('Machine stopped')
        Session().commit()
        return True

    def currentProgram(self):
        return self.machine.currentProgram

    def currentAction(self):
        return self.executor.currentAction

    def start(self):
        if self.machine:
            self.machine.state(State.START)

    def stop(self):
        if self.machine:
            self.machine.state(State.STOP)

    def shutdown(self):
        if self.machine:
            self.machine.state(State.SHUTDOWN)

    def state(self):
        return self.machine.state()

    @event
    def programBegin(self, program):
        pass

    @event
    def programComplete(self, program, status, message=None):
        pass

    @event
    def actionBegin(self, action, message):
        pass

    @event
    def actionComplete(self, action, status, message=None):
        pass

    @event
    def stateChanged(self, newState, oldState):
        pass
        
