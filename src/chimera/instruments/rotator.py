from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.rotator import Rotator


class RotatorBase(ChimeraObject, Rotator):
    def __init__(self):
        ChimeraObject.__init__(self)

    def get_position(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def move_to(self, angle):
        raise NotImplementedError("Subclasses should implement this method.")

    def sync(self, position):
        raise NotImplementedError("Subclasses should implement this method.")

    def is_moving(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def abort_move(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def move_by(self, angle):
        current_position = self.get_position()
        new_position = current_position + angle
        self.move_to(new_position)
