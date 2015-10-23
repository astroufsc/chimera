from chimera.instruments.domefan import DomeFanBase
from chimera.interfaces.domefan import FanDirection, FanStatus
from chimera.core.lock import lock


class FakeDomeFan(DomeFanBase):
    def __init__(self):
        DomeFanBase.__init__(self)

        self._currentSpeed = 0.
        self._isrunning = False
        self._currentStatus = FanStatus.STOPPED
        self._currentDirection = FanDirection.FORWARD

    def getRotation(self):
        return self._currentSpeed

    @lock
    def setRotation(self, freq):
        if float(self["min_speed"]) < freq < float(self["max_speed"]):
            self._currentSpeed = float(freq)
        else:
            raise IOError("Fan speed must be between %.2f and %.2f. Got %.2f." % (float(self["min_speed"]),
                                                                                  float(self["max_speed"]),
                                                                                  freq))

    def getDirection(self):
        return self._currentDirection

    @lock
    def setDirection(self, direction):
        if direction in FanDirection:
            self._currentDirection = direction
        else:
            self.log.warning("Value %s not a valid fan direction. Should be one of %s. Leaving unchanged." % (direction,
                                                                                                              ['%s' % d
                                                                                                               for d in
                                                                                                               FanDirection]))

    @lock
    def startFan(self):

        self._currentStatus = FanStatus.RUNNING
        self._isrunning = True

        self.fanStarted()

        return True

    @lock
    def stopFan(self):

        self._currentStatus = FanStatus.STOPPED
        self._isrunning = False

        self.fanStopped()

        return True

    def isFanRunning(self):
        return self._isrunning

    def status(self):
        return self._currentStatus
