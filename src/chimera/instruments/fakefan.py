from chimera.core.lock import lock
from chimera.instruments.fan import FanBase
from chimera.interfaces.fan import (
    FanControllableDirection,
    FanControllableSpeed,
    FanDirection,
    FanState,
    FanStatus,
)


class FakeFan(FanBase, FanState, FanControllableSpeed, FanControllableDirection):
    def __init__(self):
        FanBase.__init__(self)

        self._current_speed = 0.0
        self._is_on = False
        self._current_status = FanStatus.OFF
        self._current_direction = FanDirection.FORWARD

    def get_rotation(self):
        return self._current_speed

    @lock
    def set_rotation(self, freq):
        min_speed, max_speed = self.get_range()
        if min_speed <= freq <= max_speed:
            self._current_speed = float(freq)
        else:
            raise OSError(
                f"Fan speed must be between {min_speed:.2f} and {max_speed:.2f}. Got {freq:.2f}."
            )

    def get_range(self):
        return 0.0, 100.0

    def get_direction(self):
        return self._current_direction

    @lock
    def set_direction(self, direction):
        if direction in FanDirection:
            self._current_direction = direction
        else:
            self.log.warning(
                "Value {} not a valid fan direction. Should be one of {}. Leaving unchanged.".format(
                    direction, [f"{d}" for d in FanDirection]
                )
            )

    @lock
    def switch_on(self):
        self._current_status = FanStatus.ON
        self._is_on = True

        self.switched_on()

        return True

    @lock
    def switch_off(self):
        self._current_status = FanStatus.OFF
        self._is_on = False

        self.switched_off()

        return True

    def is_switched_on(self):
        return self._is_on

    def status(self):
        return self._current_status
