from chimera.controllers.scheduler.circular import CircularScheduler
from chimera.controllers.scheduler.executor import ProgramExecutor
from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.model import Session
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.states import State
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event import event
from chimera.util.enum import Enum


class SchedulingAlgorithm(Enum):
    SEQUENTIAL = "SEQUENTIAL"
    CIRCULAR = "CIRCULAR"


scheduling_algorithms = {
    SchedulingAlgorithm.SEQUENTIAL: SequentialScheduler(),
    SchedulingAlgorithm.CIRCULAR: CircularScheduler(),
}


def program_info(program) -> dict | None:
    """JSON-safe snapshot of a Program for the bus. Reads only its own
    columns — never the lazy .actions relation: the instance belongs to
    another thread's session and may be detached."""
    if program is None:
        return None
    return {
        "id": program.id,
        "name": program.name,
        "pi": program.pi,
        "priority": program.priority,
    }


def action_info(action) -> dict | None:
    """JSON-safe snapshot of an Action for the bus. Uses type(action).__name__
    rather than the action_type discriminator: that column is only populated
    on flush, and AutoFlat's polymorphic identity is spelled 'AutoFlats'."""
    if action is None:
        return None
    return {
        "id": action.id,
        "program_id": action.program_id,
        "type": type(action).__name__,
        "description": str(action),
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
        "autoguider": "/Autoguider/0",
        "point_verify": "/PointVerify/0",
        "operator": "/Operator/0",
        "algorithm": SchedulingAlgorithm.SEQUENTIAL,
        # left tracking, an unattended mount walks into a limit
        "stop_tracking_on_program_end": True,
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
        return program_info(self.machine.current_program)

    def current_action(self):
        return action_info(self.executor.current_action)

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
    def program_begin(self, program_id):
        pass

    @event
    def program_complete(self, program_id, status, message=None):
        pass

    @event
    def action_begin(self, action_id, message):
        pass

    @event
    def action_complete(self, action_id, status, message=None):
        pass

    @event
    def state_changed(self, new_state, old_state):
        pass
