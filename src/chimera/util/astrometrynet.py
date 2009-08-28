from subprocess import Popen
from chimera.util.sextractor import SExtractor
from chimera.core.exceptions import ChimeraException
from chimera.util.image import Image

import os
import shutil

import logging
import chimera.core.log
log = logging.getLogger(__name__)

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
            line = "solve-field %s -d 10,20,30,40,50 --overwrite -o %s --ra %f --dec %f --radius %f"  %(fullfilename, outfilename, ra, dec, radius)
        elif findstarmethod == "sex":
            sexoutfilename = pathname + outfilename + ".xyls"
            line = "solve-field %s  -d 10,20,30,40,50 --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d --ra %f --dec %f --radius %f"  %(sexoutfilename, outfilename, width, height, ra, dec, radius)
            # line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d"  %(sexoutfilename, outfilename,width, height)
            # could use --guess-scale for unreliable mounts:
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
        # *** it would be nice to add a test here to check 
        # whether astrometrynet is running OK, if not raise a new exception 
        # like AstrometryNetInstallProblem
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
        iraf.hedit(wcs_imgname,"CD1_1,CD1_2,CD2_1,CD2_2,CRPIX1,CRPIX2,CRVAL1,CRVAL2,RA,DEC,ALT,AZ",
                   add="no",addonly="no",delete="yes",
                   verify="no",show="no",update="yes")
        iraf.mkheader(images=wcs_imgname,headers=wcs_solution+".fits",
                      append="yes",verbose="no",mode="al")
        return(wcs_imgname)
  
    
class AstrometryNetException(ChimeraException):
    pass        

class NoSolutionAstrometryNetException(ChimeraException):
    pass        
        
        
if __name__ == "__main__":
    try:
        #x = AstrometryNet.solveField("/home/obs/20090721-024102-0001.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/home/obs/20090721-024102-0001.fits",findstarmethod="sex")

        #x = AstrometryNet.solveField("/home/obs/20090721-032526-0001.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/home/obs/20090721-032526-0001.fits",findstarmethod="sex")

        #x = AstrometryNet.solveField("/home/obs/20090721-040339-0001.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/home/obs/20090721-040339-0001.fits",findstarmethod="sex")

        #x = AstrometryNet.solveField("/home/obs/20090721-040645-0001.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/home/obs/20090721-040645-0001.fits",findstarmethod="sex")

        #x = AstrometryNet.solveField("/home/obs/ph/pointverify-20090720-0001.fits",findstarmethod="astrometry.net")
        #x = AstrometryNet.solveField("/home/obs/ph/pointverify-20090720-0001.fits",findstarmethod="sex")

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
        # x  = AstrometryNet.solveField("/home/kanaan/images/20090721/lna/20090721/20090721-234033-0001.fits",findstarmethod="sex") 
        # tests of fields selected by hand by Paulo and I:
        # x = AstrometryNet.solveField("/media/K2/astindices/demo/lna/2008-08-06/landolt-109231-0003.fits",findstarmethod="sex") # works
        # x = AstrometryNet.solveField("/media/K2/astindices/demo/lna/2008-08-06/lixo.fits",findstarmethod="sex") # works
        # x = AstrometryNet.solveField("/media/K2/astindices/demo/lna/2008-08-06/landolt-109231-0003.fits") # doesn't work
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/M6-0003.fits",findstarmethod="sex")  # works 
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA111773-0002.fits",findstarmethod="sex")  # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0001.fits",findstarmethod="sex")  # no stars, doesn work
        # x = AstrometryNet.solveField("/tmp/landolt-SA112223-0002.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0003.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0004.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0005.fits",findstarmethod="sex") # works
        #x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/landolt-SA112223-0005.fits",findstarmethod="sex") # works

        # files Paulo and I did with the "extinction machine"

        # x = AstrometryNet.solveField("/media/USB2/astindices/demo/lna/2008-08-06/070808-040709-0001.fits",findstarmethod="sex")
        #x = AstrometryNet.solveField("/home/obs/images/2008-10-02/021008-224939-0001.fits",findstarmethod="sex")
        # x = AstrometryNet.solveField("/home/henrique/ph/chimera/landolt-0001.fits",findstarmethod="sex")
        # x = AstrometryNet.solveField("/home/henrique/landolt-com-header.fits",findstarmethod="sex")        
	# missing HEADER keywords:
        # x = AstrometryNet.solveField("/home/kanaan/data/chimera/20090618/20090619-013107-0001.fits",findstarmethod="sex")        
        #x = AstrometryNet.solveField("/home/kanaan/data/chimera/20090629/20090629-234418-0001.fits",findstarmethod="sex")        
        # x = AstrometryNet.solveField("/home/obs/images/20090703/pointverify-20090703-0012.fits")        

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
        # x = AstrometryNet.solveField("/home/kanaan/images/20090721/lna/20090721/20090722-013518-0001.fits",findstarmethod="sex")
        x = AstrometryNet.solveField("/home/kanaan/images/20090721/lna/20090721/20090722-021624-0001.fits",findstarmethod="sex")

        x = AstrometryNet.solveField("/home/obs/20090721/20090721-230831-0001.fits",findstarmethod="sex")
        x = AstrometryNet.solveField("/home/obs/20090721/20090721-230902-0001.fits",findstarmethod="sex")
        x= AstrometryNet.solveField("/home/obs/20090721/20090721-232001-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090721-234033-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-005104-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-005127-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-005235-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-012010-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-013114-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-013518-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-020337-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-021136-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-021624-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022132-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022210-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022247-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022712-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022749-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-022827-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-023019-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-023057-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-023135-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-023859-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-023936-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024014-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024157-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024235-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024313-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024449-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-024527-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-025128-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-025509-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-025558-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-025701-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-025857-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-040456-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-040806-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-041201-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-042806-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044425-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044503-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044541-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044619-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044657-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044735-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044813-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044851-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-044929-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-045007-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-045044-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050150-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050228-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050306-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050343-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050421-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050459-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050537-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050615-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050653-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050730-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050808-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050846-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-050924-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051002-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051040-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051117-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051155-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051233-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051311-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051349-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051427-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051505-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051543-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051621-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051658-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051736-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051814-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051853-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-051930-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052008-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052046-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052124-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052202-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052240-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052318-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052355-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052433-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052511-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052549-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052627-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052705-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052743-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052821-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052859-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-052937-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053015-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053053-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053130-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053208-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053246-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053324-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053402-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053440-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053518-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053556-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053633-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053711-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053749-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053827-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053905-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-053943-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054021-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054058-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054136-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054214-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054252-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054330-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054408-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054446-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054524-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054602-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054639-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054717-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054755-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054833-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054911-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-054949-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055027-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055104-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055142-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055220-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055258-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055336-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055414-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055452-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055530-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055607-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055645-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055723-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055801-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055839-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055917-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-055955-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060033-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060111-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060149-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060226-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060304-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060342-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060420-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060458-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060536-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060614-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060652-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060729-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060807-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060845-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-060923-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061001-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061039-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061117-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061155-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061233-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061310-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061348-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061426-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061504-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061542-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061620-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061658-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061736-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061813-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061851-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-061929-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062007-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062045-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062123-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062201-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062238-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062316-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062354-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062432-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062510-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062548-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062626-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062703-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062741-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062819-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062857-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-062935-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063013-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063051-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063129-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063206-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063244-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063322-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063400-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063438-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063516-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063554-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063632-0001.fits",findstarmethod="sex")
        x=AstrometryNet.solveField("/home/obs/20090721/20090722-063709-0001.fits",findstarmethod="sex")

    except Exception, e:
        print e
