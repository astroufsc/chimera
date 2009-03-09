from subprocess import Popen
from chimera.util.sextractor import SExtractor
from chimera.core.exceptions import ChimeraException
from chimera.util.image import Image

import os
import shutil
from pyraf import iraf

import logging
import chimera.core.log
log = logging.getLogger(__name__)

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
        pathname = pathname + "/"
        basefilename,file_xtn = os.path.splitext(filename)
        # *** enforce .fits extension
        if (file_xtn != ".fits"):
            raise ValueError("File extension must be .fits it was = %s\n" %file_xtn)

        # *** check whether the file exists or not
        if ( os.path.exists(fullfilename) == False ):
            raise IOError("You selected image %s  It does not exist\n" %fullfilename)

        # version 0.23 changed behavior of --overwrite
        # I need to specify an output filename with -o
        outfilename = basefilename + "-out"

        image = Image.fromFile(fullfilename)
        try:
            ra = image["CRVAL1"]    # expects to see this in image
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        try:
            dec = image["CRVAL2"]
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        width = image["NAXIS1"]
        height = image["NAXIS2"] 
        radius = 5.0 * abs(image["CD1_1"]) * width

        if findstarmethod == "astrometry.net":
            #line = "solve-field --guess-scale %s --overwrite -o %s" %(fullfilename, outfilename)
            line = "solve-field %s --overwrite -o %s --ra %f --dec %f --radius %f"  %(fullfilename, outfilename, ra, dec, radius)
            print line


        elif findstarmethod == "sex":
            sexoutfilename = pathname + outfilename + ".xyls"
            line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d --ra %f --dec %f --radius %f"  %(sexoutfilename, outfilename, width, height, ra, dec, radius)
            print "Sextractor command line %s" %line
            # using --guess-scale
            # line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d --guess-scale"  %(sexoutfilename, outfilename, width, height)

            sex = SExtractor()
            sex.config['BACK_TYPE']   = "AUTO"
            sex.config['DETECT_THRESH'] = 3.0
            sex.config['DETECT_MINAREA'] = 18.0
            sex.config['VERBOSE_TYPE'] = "QUIET"
            sex.config['CATALOG_TYPE'] = "FITS_1.0"
            #sex.config['CATALOG_TYPE'] = "ASCII"
            sex.config['CATALOG_NAME'] = sexoutfilename
            sex.config['PARAMETERS_LIST'] = ["X_IMAGE","Y_IMAGE","MAG_ISO"]
            sex.run(fullfilename)

        else:
            log.error("Unknown option used in astrometry.net")

        # when there is a solution astrometry.net creates a file with .solved
        # added as extension.  
        is_solved = pathname + outfilename + ".solved"
        # if it is already there, make sure to delete it 
        if ( os.path.exists(is_solved)):
            os.remove(is_solved)
	print "SOLVE"  , line
        solve = Popen(line.split()) # ,env=os.environ)
        solve.wait()
        # if solution failed, there will be no file .solved
        if ( os.path.exists(is_solved) == False ):
            raise NoSolutionAstrometryNetException("Astrometry.net could not find a solution for image: %s %s" %(fullfilename, is_solved))

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
        iraf.mkheader(images=wcs_imgname,headers=wcs_solution+".fits",
                      append="no",verbose="no",mode="al")
        return(wcs_imgname)
  
    
class AstrometryNetException(ChimeraException):
    pass        

class NoSolutionAstrometryNetException(ChimeraException):
    pass        
        
        
if __name__ == "__main__":
    try:
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/NH2_a10d30.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d30.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d20.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d10.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d00.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-10.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-20.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-30.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-40.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-50.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-60.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-70.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-80.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/a10d-90.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/sequencia-3/focus-sequence-0007.fits",findstarmethod="sex")
        #x =  AstrometryNet.solveField("/media/USB2/astindices/demo/lna/landolt-point/test-point.fits",findstarmethod="sex")
        #x =  AstrometryNet.solveField("/media/USB2/astindices/demo/lna/landolt-point/test-point-dss.fits",findstarmethod="sex")
        #x =  AstrometryNet.solveField("/media/USB2/astindices/demo/lna/landolt-point/test-point-dss-300x300.fits",findstarmethod="sex")
        #x =  AstrometryNet.solveField("/media/USB2/astindices/demo/lna/landolt-point/test-point-dss-same.fits",findstarmethod="sex")
        # x = AstrometryNet.solveField("/media/USB2/astindices/demo/dss/bpm37093.fits",findstarmethod="sex") # works
        #  = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/landolt-point/test-point-subdss.fits",findstarmethod="sex") # works
        # tests of fields selected by hand by Paulo and I:
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-109231-0003.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/M6-0003.fits",findstarmethod="sex")  # works 
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA111773-0002.fits",findstarmethod="sex")  # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0001.fits",findstarmethod="sex")  # no stars, doesn work
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0002.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0003.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0004.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0005.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0005.fits",findstarmethod="sex") # works

        # files Paulo and I did with the "extinction machine"

        # x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040709-0001.fits",findstarmethod="sex")
        x = AstrometryNet.solveField("/home/obs/images/2008-10-02/021008-224939-0001.fits",findstarmethod="sex")


        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-033129-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # 
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-033150-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-033305-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-033325-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034123-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034143-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034207-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034227-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034401-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034423-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034537-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034557-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034722-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034744-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034854-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034915-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034937-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-034958-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035114-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035135-0001.fits",findstarmethod="sex")    
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035230-0001.fits",findstarmethod="sex")  
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035251-0001.fits",findstarmethod="sex")  
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035451-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035512-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035708-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035729-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035831-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-035852-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040024-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040045-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040151-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040213-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040328-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040349-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040431-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040452-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040542-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040603-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040648-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040709-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040802-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040823-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040846-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040907-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040955-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041017-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041138-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041201-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041323-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041345-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041436-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041458-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041536-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041557-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041630-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041651-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041713-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-041734-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-045305-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-045516-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-053131-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-053405-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-053616-0001.fits",findstarmethod="sex")
        # except:
        #     print "Failed"
        # try:
        #     x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-053826-0001.fits",findstarmethod="sex")
        # except:
        #    print "Failed"


    except Exception,e:
        pass
        
