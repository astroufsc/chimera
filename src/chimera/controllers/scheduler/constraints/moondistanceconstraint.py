from chimera.controllers.scheduler.constraints import IConstraint

class MoonDistanceConstraint(IConstraint):
    def getMyKey(self):
        return 'MoonDistance'
    
    def __str__(self):
        return 'Constraint based upon the distance from the moon'
    
    def checkConstraint(self, paramMin, paramMax, exposure = None, observation = None, program = None):
        if exposure == None:
            return self.DONTCARE
