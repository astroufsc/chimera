from uts.core.interface import Interface

class Dome(Interface):

    # properties
    azimute = 0
    altura = 0
    parkPosition = 0

    # methods
    def slew(self, alt, azim):
        pass
    
    def abortSlew(self):
        pass
    
    def openShutter(self):
        pass
    
    def closeShutter(self):
        pass
    
    def home(self):
        pass
    
    def park(self):
        pass

