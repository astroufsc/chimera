from pyraf import iraf

import utilities
import reduction_tools
from image_class import Image

iraf.noao.imred()
iraf.noao.imred.ccdred()

class Calibration:
 
  def __init__(self, input, writedir):
    self.inlist = input
    self.writedir = writedir

  
class MasterZero(Calibration):

  def make(self):
    reduction_tools.rmFile(self.writedir+'Zero.fits')
    inlist = reduction_tools.makeIrafList(self.inlist)

    iraf.noao.imred.ccdred.zerocombine(input=inlist, output=self.writedir+'Zero', process='no', delete='no', clobber='no')
    return Image(self.writedir+'Zero.fits')

class MasterDark(Calibration):

  def make(self, masterzero):
    reduction_tools.rmFile(self.writedir+'Dark.fits')
    mzero = masterzero.location
    inlist = reduction_tools.makeIrafList(self.inlist)
    
    iraf.noao.imred.ccdred.ccdproc(images=inlist, zerocor='yes', zero=mzero, darkcor='no', flatcor='no')

    iraf.noao.imred.ccdred.darkcombine(input=inlist, output=self.writedir+'Dark', process='no', delete='no', clobber='no', scale='exposure')
    return Image(self.writedir+'Dark.fits')
    
class MasterFlat(Calibration):

  def make(self, masterzero, masterdark):
    reduction_tools.rmFile(self.writedir+'Flat.fits')
    mzero = masterzero.location
    mdark = masterdark.location
    inlist = reduction_tools.makeIrafList(self.inlist)
    
    iraf.noao.imred.ccdred.ccdproc(images=inlist, zerocor='yes', zero=mzero, darkcor='yes', dark=mdark, flatcor='no')
    iraf.noao.imred.ccdred.flatcombine(input=inlist, output=self.writedir+'Flat', process='no', delete='no', clobber='no', scale='mode')





