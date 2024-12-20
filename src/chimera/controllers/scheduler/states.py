from chimera.util.enum import Enum

__all__ = ["State"]


class State(Enum):
    OFF = "OFF"
    START = "START"
    IDLE = "IDLE"
    BUSY = "BUSY"
    STOP = "STOP"
    SHUTDOWN = "SHUTDOWN"
