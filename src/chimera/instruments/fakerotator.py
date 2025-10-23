import time
from chimera.instruments.rotator import RotatorBase
from chimera.interfaces.rotator import RotatorStatus


class FakeRotator(RotatorBase):

    def __init__(self):
        super().__init__()
        self._position = 0.0

    def get_position(self):
        return self._position

    def abort_move(self):
        self.move_complete(self._position, RotatorStatus.ABORTED)
        return True

    def move_to(self, angle):
        self.move_begin(angle)
        time.sleep(1)  # Simulate time taken to move
        self._position = angle
        self.move_complete(angle, RotatorStatus.OK)
