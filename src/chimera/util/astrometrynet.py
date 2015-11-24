from subprocess import Popen
import os
import logging
import time

from chimera.util.sextractor import SExtractor
from chimera.core.exceptions import ChimeraException
from chimera.util.image import Image

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
        basefilename, file_xtn = os.path.splitext(filename)
        # *** enforce .fits extension
        if file_xtn != ".fits":
            raise ValueError("File extension must be .fits it was = %s\n" % file_xtn)

        # *** check whether the file exists or not
        if os.path.exists(fullfilename) == False:
            raise IOError("You selected image %s  It does not exist\n" % fullfilename)

        # version 0.23 changed behavior of --overwrite
        # I need to specify an output filename with -o
        outfilename = basefilename + "-out"

        image = Image.fromFile(fullfilename)
        try:
            ra = image["CRVAL1"]  # expects to see this in image
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        try:
            dec = image["CRVAL2"]
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        width = image["NAXIS1"]
        height = image["NAXIS2"]
        radius = 10.0 * abs(image["CD1_1"]) * width

        wcs_filename = pathname + outfilename + ".wcs"

        if findstarmethod == "astrometry.net":
            line = "solve-field %s --no-plots --overwrite -o %s --ra %f --dec %f --radius %f" % (
                fullfilename, outfilename, ra, dec, radius)
        elif findstarmethod == "sex":
            sexoutfilename = pathname + outfilename + ".xyls"
            line = "solve-field %s --no-plots --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE " \
                   "--sort-column MAG_ISO --sort-ascending --width %d --height %d --ra %f --dec %f --radius %f" % (
                       sexoutfilename, outfilename, width, height, ra, dec, radius)

            sex = SExtractor()
            sex.config['BACK_TYPE'] = "AUTO"
            sex.config['DETECT_THRESH'] = 3.0
            sex.config['DETECT_MINAREA'] = 18.0
            sex.config['VERBOSE_TYPE'] = "QUIET"
            sex.config['CATALOG_TYPE'] = "FITS_1.0"
            sex.config['CATALOG_NAME'] = sexoutfilename
            sex.config['PARAMETERS_LIST'] = ["X_IMAGE", "Y_IMAGE", "MAG_ISO"]
            sex.run(fullfilename)

        else:
            log.error("Unknown option used in astrometry.net")

        # when there is a solution astrometry.net creates a file with .solved
        # added as extension.
        is_solved = pathname + outfilename + ".solved"
        # if it is already there, make sure to delete it
        if os.path.exists(is_solved):
            os.remove(is_solved)
        log.debug("SOLVE %s" % line)
        # *** it would be nice to add a test here to check
        # whether astrometrynet is running OK, if not raise a new exception
        # like AstrometryNetInstallProblem
        log.debug('Starting solve-field...')
        t0 = time.time()
        solve = Popen(line.split())  # ,env=os.environ)
        solve.wait()
        log.debug('Solve field finished. Took %3.2f sec' % (time.time() - t0))
        # if solution failed, there will be no file .solved
        if (os.path.exists(is_solved) == False):
            raise NoSolutionAstrometryNetException(
                "Astrometry.net could not find a solution for image: %s %s" % (fullfilename, is_solved))

        return wcs_filename


class AstrometryNetException(ChimeraException):
    pass


class NoSolutionAstrometryNetException(ChimeraException):
    pass
