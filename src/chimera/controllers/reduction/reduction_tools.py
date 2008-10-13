
import os
import shutil
import sys
from glob import glob

from pyraf import iraf

iraf.images()
iraf.noao.imred()
iraf.noao.imred.ccdred()


def rmExistingDir(directory):
    """Removes a directory
    @param directory:
    @type directory: str
    """
    check = os.path.exists(directory)
    if check:
        shutil.rmtree(directory)
        print "Directory '%s' removed" % directory
    else:
        print "Directory '%s' does not exist; '%s' not removed"
        
def rmFile(fileroot):
    """Removes file(s) based on root name of the file
    @param fileroot: <root>*
    @type fileroot: str 
    """
    del_list = glob(fileroot+'*')
    for file in del_list:
        os.remove(file)
        print "File %s removed" % file

def makeDir(newdir):
    while(1):
        if os.path.exists(newdir):
            print "Directory %s already exists" % newdir
            return newdir
            break
        else:
            os.mkdir(newdir)
            print "New Directory '%s' created" % newdir
            return newdir
            break

def copyNewFits(imlist, destdir):
    """Copies all files in a python list to certain destination directory
    @param imlist: images to be copied
    @type imlist: list
    @param destdir: destination directory
    @type destdir: str
    """
    copiedlist = []
    
    if not os.path.exists(destdir):
        os.mkdir(destdir)
    for im in imlist:
        if os.path.isfile(im):
            if not os.path.isfile(destdir+os.path.split(im)[-1]):
                shutil.copy(im, destdir)
                newloc = destdir+os.path.split(im)[-1]
                print "Copied %s to %s" % (im, destdir)
                copiedlist.append(newloc)
    
    return copiedlist
        
    
    