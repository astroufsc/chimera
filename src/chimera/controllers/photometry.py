
from chimera.core.chimeraobject import ChimeraObject

class Photometry (ChimeraObject):

    def __start__ (self):
        self.reducer = self.getManager().getProxy("/Reduction/0")
        self.reducer.reductionComplete += self.calibrate

    def calibrate (self, imageRequest):
        self.calibrationDone(imageRequest)
