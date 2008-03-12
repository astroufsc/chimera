
class TelescopeLimits (object):

    def __init__ (self):
        # list with 360 (one for each azimuth) with the max zenital distance
        # allowed to slew
        self.limits = []

    def load (self, filename):
        pass

    def isAllowed (self, az, alt):
        pass
