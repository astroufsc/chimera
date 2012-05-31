from chimera.util.enum import Enum

__all__ = ['State']

State = Enum("OFF", "START", "IDLE", "BUSY", "STOP", "SHUTDOWN")
