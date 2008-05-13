
import os
import os.path
import tempfile
import string
import random
import tempfile
import pwd
import logging
import time
import sys

# ask to use numpy
os.environ["NUMERIX"] = "numpy"
import pyfits

import numpy

import chimera.core.log
log = logging.getLogger(__name__)

from chimera.interfaces.cameradriver import Bitpix
from chimera.util.filenamesequence import FilenameSequence

class ImageSave (object):


    @staticmethod
    def getPixels (ccd_with, ccd_height, width, height, bitpix):
        """
        Returns a numpy matrix that could be used as pixels for an
        image on the CCD with ccd_width X ccd_height pixels given the
        window contrainsts on x, y, width, height using the rules
        describe at L{ICamera} for window specification and using the
        selected bitpix.
        """
        bitpix = self._getBitPix()

        # start readout
        img = numpy.zeros(self.drv.readoutModes[self.ccd][readoutMode].getSize(), bitpix)
        

    @staticmethod
    def save (img,
              directory="$HOME/images", filename="$date", ext="fits",
              dateFormat="%d%m%y-%H%M%S", obsTime=None,
              bitpix=Bitpix.int16, saveOnTemp=True, dry=False):
        """
        Save the image matrix given in img. This save is very
        cautious, it checks if the file already exists and if the user
        have rights to wrote on that location. In addition, user can
        provide string templates to both directory and
        filename(environment variables are allowed on direcotory
        also).
        """
        
        # check if config.directory exists
        # also check write permissions. If user don't have permission, try to write on /tmp
        # and log this so user can try to copy this later

        dest = directory

        dest = os.path.expanduser(dest)
        dest = os.path.expandvars(dest)
        dest = os.path.realpath(dest)

        # existence of the directory
        if not os.path.exists(dest):

            # directory doesn't exist, check config to know what to do
            if not saveOnTemp:
                raise IOError("The direcotry specified (%s) doesn't exist "
                              "and save_on_temp was not active, the current "
                              "exposure will be lost." % (dest))
                
            else:
                log.warning("The direcotry specified (%s) doesn't exist. "
                            "save_on_temp is active, the current exposure will be saved on /tmp" % (dest))

                dest = tempfile.gettempdir ()
                       
        # permission
        if not os.access(dest, os.W_OK):
            # user doesn't have permission to write on dest, check config to know what to do
            uid = os.getuid()
            user = pwd.getpwuid(uid)[0]

            if not saveOnTemp:
                raise IOError("User %s (%d) doesn't have permission to write "
                              "on %s and save_on_temp was not active, the current "
                              "exposure will be lost." % (user, uid, dest))
            else:
                log.warning("User %s (%d) doesn't have permission to write on %s. "
                            "save_on_temp is active, the current exposure will be saved on /tmp" % (user, uid, dest))
                

        # create filename
        # FIXME: UTC or not UTC?
        subs_dict = {"date": time.strftime(dateFormat, time.gmtime(obsTime))}

        filename = string.Template(filename).safe_substitute(subs_dict)

        seq_num = FilenameSequence(os.path.join(dest, filename), extension=ext).next()

        finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, seq_num, os.path.extsep, ext))

        # check if the finalname doesn't exist
        if os.path.exists(finalname):
            tmp = finalname
            finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, int (random.random()*1000),
                                                            os.path.extsep, ext))
            
            log.debug ("Image %s already exists. Saving to %s instead." %  (tmp, finalname))

	# dry run, just to get next available filename
	if dry:
	    return finalname
            
        try:
            hdu  = pyfits.PrimaryHDU(img)
            
            if bitpix == Bitpix.uint16:
                hdu.scale('int16', '', bzero=32768, bscale=1)

            # add basic header (DATE, DATE-OBS) as this information can get lost
            # any other header should be added later by the controller
            fits_date_format = "%Y-%m-%dT%H:%M:%S"
            file_date = time.strftime(fits_date_format, time.gmtime())

            if not obsTime:
                obsTime = time.gmtime()
                                     
            obs_date = time.strftime(fits_date_format, time.gmtime(obsTime))
            
            hdu.header.update("DATE", file_date, "date of file creation")
            hdu.header.update("DATE-OBS", obs_date, "date of the observation")

            fits = pyfits.HDUList([hdu])
            fits.writeto(finalname)
            
        except IOError:
            log.error("An error ocurred trying to save on %s. "
                      "The current image will be lost. "
                      "Exception follow" %  finalname)
            raise

            
        return finalname


