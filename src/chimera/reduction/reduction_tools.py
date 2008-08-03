
import os
import shutil
import sys
from pyraf import iraf
from glob import *

import utilities
from image_class import *

iraf.images()
iraf.noao.imred()
iraf.noao.imred.ccdred()


def rmExistingDir(directory):
  check=os.path.exists(directory)
  if check==True:
    shutil.rmtree(directory)
    print "Directory '%s' removed" % directory
  else: 
    print "Directory '%s' does not exist; '%s' not removed" % (directory, directory)

def rmFile(filename):
  check=os.path.isfile(filename)
  if check==True:
    os.remove(filename)
    print "File %s removed" % filename
  else:
    print "File '%s' does not exist; '%s' not removed" % (filename, filename)

def makeDir(newdir):
  if os.path.exists(newdir)==True:
    shutil.rmtree(newdir)
    print "Overwriting '%s'" % (newdir)
  os.mkdir(newdir)
  print "New directory '%s' created" % newdir

def copyFits(imist, destdir):
  if os.path.exists(destdir)==False:
    os.mkdir(destdir)
  for im in imlist:
    if utilities.isstr(im)==False:
      im=str(im)
    shutil.copy(im, destdir)
   
def makeIrafList(inlist):
  newlist = ''
  for im in inlist:
    newlist = newlist +im.location + ','+' '
  newlist = '"'+newlist+'"'
  return newlist 

def filter(imobjlist, param):

  stolist=[]
  typelist=[]
  while len(imobjlist)!=0:
    newlist=[]  
    primero=imobjlist[0]
    parameter=primero.getParam(param)
    newlist.append(primero)
    del imobjlist[0]

    i=0
    for image in imobjlist:
      if image.getParam(param)==parameter:
        newlist.append(image)
        del imobjlist[i]
      i+=1
    
    stolist.append(newlist)
    typelist.append(parameter)

  return stolist, typelist

def _add(imobjone, imobjtwo, writeloc):
  locone = imobjone.location
  loctwo = imobjone.location
  iraf.imarith(operand1 = locone, op = '+', operand2 = loctwo, result = writeloc)
  return Image(writeloc)

def _subtract(imobjone, imobjtwo, writeloc):
  locone = imobjone.location
  loctwo = imobjone.location
  iraf.imarith(operand1 = locone, op = '-', operand2 = loctwo, result = writeloc)
  return Image(writeloc)

def _multiply(imobjone, imobjtwo, writeloc):
  locone = imobjone.location
  loctwo = imobjone.location
  iraf.imarith(operand1 = locone, op = '*', operand2 = loctwo, result = writeloc)
  return Image(writeloc)

def _divide(imobjone, imobjtwo, writeloc):
  locone = imobjone.location
  loctwo = imobjone.location
  iraf.imarith(operand1 = locone, op = '/', operand2 = loctwo, result = writeloc) 
  return Image(writeloc)
