from chimera.util.enum import Enum


class SchedulerStatus(Enum):
    OK = "OK"
    ABORTED = "ABORTED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
