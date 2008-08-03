from chimera.util.enum import Enum

ConstraintReturns = Enum('GOOD', 'BAD', 'DONTCARE')

__all__=['ConstraintReturns']

class Constraints:
    
    def __init__(self):
        self.__constraints={'MoonDistance': MoonDistanceConstraint()}
    
    def checkConstraint(self, constraintName, paramMin, paramMax, exposure = None, observation = None, program = None):
        return self.__constraints[constraintName].checkConstraint(paramMin, paramMax, exposure = None, observation = None, program = None)

class IConstraint:
    
    def __init__(self):
        self.DONTCARE=ConstraintReturns.DONTCARE
        self.GOOD=ConstraintReturns.GOOD
        self.BAD=ConstraintReturns.BAD
    
    """
    Return the name by which this constraint is referenced.
    """
    def getMyKey(self):
        raise "This module failed to export its key." 
    
    """
    Return the description of this constraint
    """
    def getMyDescription(self):
        return self.__str__
    
    """
    Check whether this constraint is satisfied
    """
    def checkConstraint(self, paramMin, paramMax, exposure = None, observation = None, program = None):
        return ConstraintReturns.DONTCARE
        raise "This module didn't check any constraints."

