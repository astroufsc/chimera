from enum import Enum
from chimera.core.event import event
from chimera.core.interface import Interface


class RotatorStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class Rotator(Interface):
    """
    Interface for telescope rotators. Allows control of the rotator position
    and monitor the current position.
    """

    __config__ = {
        "device": None,
        "rotator_model": "",
    }

    def get_position(self) -> float:
        """
        Get the current rotator position.

        @return: The current position in degrees.
        @rtype: float
        """

    def move_to(self, position: float) -> None:
        """
        Set the rotator position.

        @param position: The position to set in degrees.
        @type  position: float
        @rtype: None
        """

    def move_by(self, angle: float) -> None:
        """
        Move the rotator by a relative angle.

        @param angle: The angle to move by in degrees.
        @type  angle: float
        @rtype: None
        """

    @event
    def slew_begin(self, angle: float) -> None:
        """
        Rotator slew begins.

        @param angle: The new position in degrees.
        @type  angle: float
        """

    @event
    def slew_complete(self, angle: float, status: RotatorStatus) -> None:
        """
        Rotator slew is complete.

        @param angle: The current position in degrees.
        @type  angle: float
        @param status: The status of the slew operation.
        @type  status: RotatorStatus
        """
