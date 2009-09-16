from chimera.util.enum import Enum

__all__ = ['State']

State = Enum("OFF", "DIRTY", "IDLE", "BUSY", "PAUSED", "SHUTDOWN")
