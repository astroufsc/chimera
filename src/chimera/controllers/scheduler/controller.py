from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.circular import CircularScheduler
from chimera.controllers.scheduler.executor import ProgramExecutor
from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.model import Session

from chimera.util.enum import Enum


class SchedulingAlgorithm(Enum):
    SEQUENTIAL = "SEQUENTIAL"
    CIRCULAR = "CIRCULAR"


scheduling_algorithms = {
    SchedulingAlgorithm.SEQUENTIAL: SequentialScheduler(),
    SchedulingAlgorithm.CIRCULAR: CircularScheduler(),
}


class Scheduler(ChimeraObject):

    __config__ = {
        "telescope": "/Telescope/0",
        "rotator": "/Rotator/0",
        "camera": "/Camera/0",
        "filterwheel": "/FilterWheel/0",
        "focuser": "/Focuser/0",
        "dome": "/Dome/0",
        "autofocus": "/Autofocus/0",
        "autoflat": "/Autoflat/0",
        "point_verify": "/PointVerify/0",
        "site": "/Site/0",
        "algorithm": SchedulingAlgorithm.SEQUENTIAL,
    }

    def __init__(self):
        ChimeraObject.__init__(self)

        self.executor = None
        self.scheduler = None
        self.machine = None

    def __start__(self):
        self.executor = ProgramExecutor(self)
        self.scheduler = scheduling_algorithms[self["algorithm"]]
        self.machine = Machine(self.scheduler, self.executor, self)

        self.log.debug("Using {} algorithm".format(self["algorithm"]))

    def control(self):
        if not self.machine.is_alive():
            self.machine.start()
            return False

    def __stop__(self):
        self.log.debug("Attempting to stop machine")
        self.shutdown()
        self.log.debug("Machine stopped")
        Session().commit()
        return True

    def current_program(self):
        return self.machine.current_program

    def current_action(self):
        return self.executor.current_action

    def start(self):
        if self.machine:
            self.machine.state(State.START)

    def stop(self):
        if self.machine:
            self.machine.state(State.STOP)

    def shutdown(self):
        if self.machine:
            self.machine.state(State.SHUTDOWN)

    def restart_all_programs(self):
        if self.machine:
            self.machine.restart_all_programs()

    def state(self):
        return self.machine.state()

    @event
    def program_begin(self, program):
        pass

    @event
    def program_complete(self, program, status, message=None):
        pass

    @event
    def action_begin(self, action, message):
        pass

    @event
    def action_complete(self, action, status, message=None):
        pass

    @event
    def state_changed(self, new_state, old_state):
        pass
