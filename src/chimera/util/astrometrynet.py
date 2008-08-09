from subprocess import Popen
from chimera.util.sextractor import SExtractor
from chimera.core.exceptions import ChimeraException
import os
import shutil
from pyraf import iraf

class AstrometryNet:
    
    # staticmethod allows to use a single method of a class
    @staticmethod
    def solveField(fullfilename, findstarmethod="astrometry.net"):
        """
        @param: fullfilename entire path to image
        @type: str

        @param: findstarmethod (astrometry.net, sex) 
        @type: str

        Does astrometry to image=fullfilename
        Uses either astrometry.net or sex(tractor) as its star finder

        """

        pathname, filename = os.path.split(fullfilename)
        basefilename,file_xtn = os.path.splitext(filename)
        # *** enforce .fits extension
        if (file_xtn != ".fits"):
            raise ValueError("File extension must be .fits it was = %s\n" %file_xtn)
        # *** check whether the file exists or not
        if ( os.path.exists(fullfilename) == False ):
            raise IOError("You selected image %s.  It does exist\n" %fullfilename)

        # version 0.23 changed behavior of --overwrite
        # I need to specify an output filename with -o
        outfilename = basefilename + "-out"

        if findstarmethod == "astrometry.net":
            line = "solve-field --guess-scale %s --overwrite -o %s" %(fullfilename, outfilename)

        elif findstarmethod == "sex":
            sex = SExtractor()
            sex.config['BACK_TYPE']   = "AUTO"
            sex.config['DETECT_THRESH'] = 3.0
            sex.config['VERBOSE_TYPE'] = "QUIET"
            sex.config['CATALOG_TYPE'] = "FITS_1.0"
            #sex.config['CATALOG_TYPE'] = "ASCII"
            sexoutfilename = pathname + basefilename + ".xyls"
            sex.config['CATALOG_NAME'] = sexoutfilename
            sex.config['PARAMETERS_LIST'] = ["X_IMAGE","Y_IMAGE","MAG_ISO"]
            sex.run(fullfilename)
            line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d"  %(sexoutfilename, outfilename, 1530, 1020)
            print "LINE = line"

        else:
            self.log.error("Unknown option used in astrometry.net")
        print "LINE", line
        # when there is a solution astrometry.net creates a file with .solve
        # added as extension.  
        is_solved = pathname + outfilename + ".solved"
        print is_solved
        # if it is already there, make sure to delete it 
        if ( os.path.exists(is_solved)):
            os.remove(is_solved)
        solve = Popen(line.split()) # ,env=os.environ)
        solve.wait()
        # if solution failed, there will be no file .solved
        if ( os.path.exists(is_solved) == False ):
            raise AstrometryNetException("Astrometry.net could not find a solution for image: %s" %fullfilename)

        # wcs_imgname will be the old fits file with the new header
        # wcs_solution is the solve-field solution file
        wcs_imgname = pathname + outfilename + "-wcs" + ".fits"
        wcs_solution = pathname + outfilename + ".wcs"
        shutil.copyfile(wcs_solution,wcs_solution+".fits")
        if ( os.path.exists(wcs_imgname) == True ):
            iraf.imdelete(wcs_imgname)

        # create a separate image with new header
        iraf.artdata()
        iraf.imcopy(fullfilename,wcs_imgname)
        print "Changing header" 
        iraf.mkheader(images=wcs_imgname,headers=wcs_solution+".fits",
                      append="no",verbose="no",mode="al")
        return(wcs_imgname)
  
    
class AstrometryNetException(ChimeraException):
    pass        
        
        
if __name__ == "__main__":
    try:
        x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/NH2_a10d30.fits",findstarmethod="sex")
    except Exception,e:
        print e
        
