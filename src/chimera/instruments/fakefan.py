from chimera.instruments.fan import FanBase
from chimera.interfaces.fan import FanControllabeSpeed, FanControllabeDirection, FanDirection, FanStatus
from chimera.core.lock import lock


class FakeFan(FanBase,FanControllabeSpeed,FanControllabeDirection):
    def __init__(self):
        FanBase.__init__(self)

        self._currentSpeed = 0.
        self._isrunning = False
        self._currentStatus = FanStatus.STOPPED
        self._currentDirection = FanDirection.FORWARD

    def getRotation(self):
        return self._currentSpeed

    @lock
    def setRotation(self, freq):
        min_speed,max_speed = self.getRange()
        if min_speed < freq < max_speed:
            self._currentSpeed = float(freq)
        else:
            raise IOError("Fan speed must be between %.2f and %.2f. Got %.2f." % (min_speed,
                                                                                  max_speed,
                                                                                  freq))

    def getRange(self):
        return (0.,100.)

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
