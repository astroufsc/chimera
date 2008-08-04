from subprocess import Popen
from chimera.core.exceptions import ChimeraException
import os
import shutil
from pyraf import iraf

class AstrometryNet:
    
    # staticmethod allows to use a single method of a class
    @staticmethod
    def solveField(filename):
        basefilename,file_xtn = os.path.splitext(filename)
        # *** enforce .fits extension
        if (file_xtn != ".fits"):
            raise ValueError("File extension must be .fits it was = %s\n" %file_xtn)
        # *** check whether the file exists or not
        if ( os.path.exists(filename) == False ):
            raise IOError("You selected image %s.  It does exist\n" %filename)
        os.environ["PATH"] += os.pathsep + "/media/USB2/astrometry/bin/"
        line = "/media/USB2/astrometry/bin/solve-field --guess-scale %s --overwrite" %filename
        # when there is a solution astrometry.net creates a file with .solve
        # added as extension.  
        is_solved = basefilename + ".solved"
        # if it is already there make sure to delete it 
        if ( os.path.exists(is_solved)):
            os.remove(is_solved)
        solve = Popen(line.split(),env=os.environ)
        solve.wait()
        # if solution failed there will be no file .solved
        # *** it is returning False when it should return True
        if ( os.path.exists(is_solved) == False ):
            print "Nao achou .solved %s" %is_solved 
            raise AstrometryNetException("Astrometry.net could not find a solution for image: %s" %filename)
        # *** why is this?  I delete the file after I create it
        wcs_imgname = basefilename + "-wcs" + ".fits"
        wcs_solution = basefilename + ".wcs"
        shutil.copyfile(wcs_solution,wcs_solution+".fits")
        if ( os.path.exists(wcs_imgname) == True ):
            iraf.imdelete(wcs_imgname)
        # create a separate image with new header
        print "Copying"
        iraf.artdata()
        iraf.imcopy(filename,wcs_imgname)
        #iraf.mkheader.setParam(image,wcs_imgname)
        #iraf.mkheader.setParam(headers,wcs_solution+".fits") # in order for this to work, it needs a .fits extension
        #iraf.mkheader.setParam(append,no)
        #iraf.mkheader.setParam(verbose,no)
        #iraf.mkheader.setParam(mode,al)
        print "Changing header" 
        iraf.mkheader(images=wcs_imgname,headers=wcs_solution+".fits",append="no",verbose="no",mode="al")
        return(wcs_imgname)
  
        
        
    
class AstrometryNetException(ChimeraException):
    pass        
        
        
if __name__ == "__main__":
    try:
        x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/NH1_a10d30.fits")
    except Exception,e:
        print e
        
    print "buda",x
