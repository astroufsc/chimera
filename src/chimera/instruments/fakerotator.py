import time
from chimera.instruments.rotator import RotatorBase
from chimera.interfaces.rotator import RotatorStatus


class FakeRotator(RotatorBase):

    def __init__(self):
        super().__init__()
        self._position = 0.0

    def get_position(self):
        return self._position

    def move_to(self, angle):
        self.slew_begin(angle)
        time.sleep(1)  # Simulate time taken to move
        self._position = angle
        self.slew_complete(angle, RotatorStatus.OK)
