import os
import shutil
import sys
from pyraf import iraf

import utilities
import reduction_tools
import calibration
from image_class import *

class Pipe:

  def __init__(self, calibinput, scienceinput, writedir, output):
    self.cin = calibinput
    self.sin = scienceinput
    self.writeto = writedir
    self.out = output

  @staticmethod
  def dirTOimobjlist(input):
    """If 'input' is a Directory, convert it to a list.  If it is already a list, do nothing"""

    type = utilities.getInType(input)
    if type=='Directory':
      imloc = input
      imobjlist = []
      inputlist = os.listdir(input)
      inlen = len(inputlist)
      for i in range(inlen):
        print inputlist[i]
        imobjlist.append(Image(imloc+'/'+inputlist[i]))
      return imobjlist
        
      
    elif type=='ImageList':
      print "input is list, doing nothing, returning input"
      return input
      
    else:
      print "Not a valid pipeline input!"

  def reduce(self):
    
    storiginals = self.writeto+'ScienceOriginals/'
    tempdir = self.writeto+'tmp/'
    streduced = self.writeto+'ReducedImages/'

    reduction_tools.rmExistingDir(storiginals)
    reduction_tools.rmExistingDir(tempdir)
    reduction_tools.rmExistingDir(streduced)
   
    reduction_tools.makeDir(storiginals)
    reduction_tools.makeDir(tempdir)
    reduction_tools.makeDir(streduced)
 
    print self.cin
    print os.listdir(self.cin)
    clist = Pipe.dirTOimobjlist(self.cin)
    slist = Pipe.dirTOimobjlist(self.sin)
    mlist = []
    redlist = []
 
    csplit, ctype = reduction_tools.filter(clist, 'imtype')

    zeroindex = ctype.index('zero')   
    darkindex = ctype.index('dark') 
    flatindex = ctype.index('flat')

    zerolist = csplit[zeroindex]
    darklist = csplit[darkindex]
    flatlist = csplit[flatindex]
    
    for im in darklist:
      print im.location

    zero = calibration.MasterZero(zerolist, self.writeto)
    mzero = zero.make()
    mlist.append(mzero)
    print mzero.location
    for im in darklist:
      print im.location
    dark = calibration.MasterDark(darklist, self.writeto)
    mdark = dark.make(mzero)
    mlist.append(mdark)

    flat = calibration.MasterFlat(flatlist, self.writeto)
    mflat = flat.make(mzero, mdark)
    mlist.append(mflat)

    i = 0
    for im in slist:
      reduction_tools.rmFile(tempdir+'tmp_a.fits')
      reduction_tools.rmFile(tempdir+'tmp_b.fits')
      redtitle = 'ReducedImage_'+str(i+1)     
      redloc = streduced+'ReducedScience_'+str(i+1)

      tmp_a = reduction_tools._subtract(im, mzero, tempdir+'tmp_a.fits')
      tmp_b = reduction_tools._subtract(tmp_a, mdark, tempdir+'tmp_b.fits')
      redim = reduction_tools._divide(tmp_b, mflat, redloc)
      redim.name = redtitle
      redlist.append(redim)
      print "Reduction no. %i saved to %s" % ((i+1), redloc) 
      i+=1 
    
