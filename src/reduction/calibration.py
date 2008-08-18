from pyraf import iraf

import reduction_tools

iraf.noao.imred()
iraf.noao.imred.ccdred()

class Calibration:
    """The Calibration class contains methods to create master calibration images."""
 
    def __init__(self, caliblocation, writeto = 'Masters/'):
        """@param caliblocation: location of individual calibration images.
        @type caliblocation: str
        @param writeto: directory to which master calibrations are written. default is 'Masters/' created within the calibdirectory
        @type writeto: str
        """ 
        self.calimages = caliblocation
        self.writedir = caliblocation+writeto
        
    def makeZero(self):
        """Wrapper for iraf routine zerocombine.  Takes .fits with header imagetyp=zero and makes a master zero."""
        reduction_tools.rmFile(self.writedir+'Zero*')
        iraf.noao.imred.ccdred.zerocombine(input=self.calimages+'*', output=self.writedir+'Zero', process='no', delete='no', clobber='no')

    def makeDark(self):
        """Wrapper for iraf routine darkcombine.  Takes .fits with headers imagetyp=dark and makes a master dark."""
        reduction_tools.rmFile(self.writedir+'Dark*')    
        iraf.noao.imred.ccdred.darkcombine(input=self.calimages+'*', output=self.writedir+'Dark', process='no', delete='no', clobber='no')
    
    def makeFlat(self):
        """Wrapper for iraf routine flatcombine.  Takes .fits with headers imagetyp=flat and makes a master flat."""
        reduction_tools.rmFile(self.writedir+'Flat*')
        iraf.noao.imred.ccdred.flatcombine(input=self.calimages+'*', output=self.writedir+'Flat', process='no', delete='no', clobber='no', subset='yes')





