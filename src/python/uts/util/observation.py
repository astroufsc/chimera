
from catalog import Object

class Observation(object):

    def __init__(self, target = None):
        self.obj = Object()
        self.nexp = 0
        self.exptime = 0
        self.filter = 0
        self.path = ""
        self.filenameIndex = 0
        self.observationTime = None
        self.frameType = None

        if(target):
            self.fromList(target)

    def fromList(self, target):
        self.obj = Object(target[1], target[2], target[3])
        self.nexp = target[4]
        self.exptime = target[5]
        self.filter = target[6]
        self.path = target[7]
        self.filenameIndex = 0
        self.observationTime = None
        self.frameType = target[0]

    def __repr__(self):           
        s = "%s %s %s\n#%s exposures of %s seconds each." % (self.obj.name, self.obj.ra, self.obj.dec, self.nexp, self.exptime)
        return s
        
class ObservationPlan(object):

    def __init__(self):

        self.observations = []

    def __len__(self):
        return len(self.observations)

    def __iter__(self):
        return iter(self.observations)

    def addObservation(self, obs):
        self.observations.append(obs)

