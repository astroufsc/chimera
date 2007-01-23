import os
import time
import logging
import pwd
import threading
import string
import random

# ask to use numpy
os.environ["NUMERIX"] = "numpy"
import pyfits
        
from sbigdrv import *

from uts.core.lifecycle import BasicLifeCycle
from uts.interfaces.camera import ICameraDriver
        
class SBIG(BasicLifeCycle, ICameraDriver):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.drv = SBIGDrv()
        self.ccd = SBIGDrv.imaging

        self.term = threading.Event()

    def init(self, config):

        self.config += config

        if self.config.ccd == "imaging":
            self.ccd = SBIGDrv.imaging
        else:
            self.ccd = SBIGDrv.tracking
            
        if self.config.device == "usb":
            self.dev = SBIGDrv.usb
        else:
            self.dev = SBIGDrv.lpt1
                        
        self.open(self.dev)

    def shutdown(self):
        self.close ()

    def control(self):
        pass

    def open(self, device):

        if not self.drv.openDriver():
            logging.error("Error opening driver: %d %s." % self.drv.getError())
            return False

        if not self.drv.openDevice(device):
            logging.error("Error opening device: %d %s." % self.drv.getError())
            return False

        if not self.drv.establishLink():
            logging.error("Error establishing link: %d %s." % self.drv.getError())
            return False

        if not self.drv.queryCCDInfo():
            logging.error("Error querying ccd: %d %s." % self.drv.getError())
            return False
        
    def close(self):
        self.drv.closeDevice()
        self.drv.closeDriver()

    def ping(self):
        return self.drv.isLinked()

    def exposing(self):
        return self.drv.exposing(self.ccd)

    def expose(self, config):

        self.config += config
        
        self.term.clear()

        if self._expose():
            self._readout()
            return True
                
        return False

    def abortExposure(self, config):

        self.config += config

        if not self.exposing():
            logging.debug("There are no exposition in course... abort cancelled.")
            return False
                
        self.term.set()

        logging.debug("Aborting exposure...")

        return True

    def _expose(self):

        if self.config.shutter == "open":
            shutter = SBIGDrv.openShutter
        elif self.config.shutter == "close":
            shutter = SBIGDrv.closeShutter
        elif self.config.shutter == "leave":
            shutter = SBIGDrv.leaveShutter
        else:
            logging.error("Incorrect shutter option (%s). Leaving shutter intact" % self.config.shutter)
            shutter = SBIGDrv.leaveShutter

        if not self.drv.startExposure(self.ccd, self.config.exp_time, shutter):
            err = self.drv.getError()
            logging.error("Error starting exposure: %d %s" %  (err))
            return False
        
        # save time exposure started
        self.config.start_time = time.time()

        while self.drv.exposing(self.ccd):
                                        
            # check if user asked to abort
            if self.term.isSet():
                # ok, abort and check if user asked to do a readout anyway
                self._endExposure()
                
                if self.config.readout_aborted:
                    self._readout()
                    
                return False

        # end exposure and returns
        self._endExposure()

        return True

    def _endExposure(self):

        if not self.drv.endExposure(self.ccd):
            err = self.drv.getError()
            logging.error("Error ending exposure: %d %s" % err)
            return False

        # fire exposeComplete event
        self.exposeComplete()

        return True

    def _readout(self):

        # start readout
        # FIXME: bitpix selection
        img = numpy.zeros(self.drv.readoutModes[self.ccd][self.config.readout_mode].getSize(), numpy.int16)

        if not self.drv.startReadout(self.ccd, 0):
            err = self.drv.getError()
            logging.error("Error starting readout: %d %s" % err)
            return False

        i = 0
        for line in range(self.drv.readoutModes[self.ccd][self.config.readout_mode].height):
            img[i] = self.drv.readoutLine(self.ccd, 0)
            i = i + 1

            # check if user asked to abort
            if self.term.isSet():
                self._endReadout()
                self._saveFITS(img)
                                
                return True

            # end readout and save
            self._endReadout()
            self._saveFITS(img)
                
            return True

    def _saveFITS(self, img):
        
        # check if config.directory exists
        # also check write permissions. If user don't have permission, try to write on /tmp
        # and log this so user can try to copy this later

        dest = self.config.directory

        dest = os.path.expanduser(dest)
        dest = os.path.expandvars(dest)
        dest = os.path.realpath(dest)
        
        # existence of the directory
        if not os.path.exists(dest):
            # directory doesn't exist, check config to know what to do
            if not self.config.save_on_temp:
                logging.warning("The direcotry specified (%s) doesn't exist "
                                "and save_on_temp was not active, the current"
                                "exposure will be lost." % (dest))
                
                return False
                        
        # permission
        if not os.access(dest, os.W_OK):
            # user doesn't have permission to write on dest, check config to know what to do
            if not self.config.save_on_temp:

                uid = os.getuid()
                user = pwd.getpwuid(uid)[0]
                logging.warning("User %s (%d) doesn't have permission to write"
                                "on %s and save_on_temp was not active, the current"
                                "exposure will be lost." % (user, uid, dest))
                
                return False

        # create filename
        # FIXME: UTC or not UTC?
        date = time.strftime(self.config.date_format, time.gmtime(self.config.start_time))
        subs_dict = {'num': self.config.seq_num,
                     'observer': self.config.observer,
                     'date': date,
                     'objname': self.config.obj_name}
        
        filename = string.Template(self.config.file_format).safe_substitute(subs_dict)
        finalname = os.path.join(dest, "%s%s%s" % (filename, os.path.extsep, self.config.file_extension))

        # check if the finalname doesn't exist
        if os.path.exists(finalname):
            tmp = finalname
            finalname = os.path.join(dest, "%s-%d%s%s" % (filename, int (random.random()*1000),
                                                          os.path.extsep, self.config.file_extension))
            
            logging.debug ("Image %s already exists. Saving to %s instead." %  (tmp, finalname))
            
            
            try:
                hdu  = pyfits.PrimaryHDU(img)

                # add basic header (DATE, DATE-OBS) ad this information can get lost
                # any other header should be added later by the controller
                fits_date_format = "%Y-%m-%dT%H:%M:%S"
                date = time.strftime(fits_date_format, time.gmtime())
                dateobs = time.strftime(fits_date_format, time.gmtime(self.config.start_time))
                
                hdu.header.update("DATE", date, "date of file creation")
                hdu.header.update("DATE-OBS", dateobs, "date of the observation")
                
                fits = pyfits.HDUList([hdu])
                fits.writeto(finalname)
                
            except IOError, e:
                logging.error("An error ocurred trying to save on %s."
                              "The current image will be lost."
                              "Exception follow" %  finalname)
                
                logging.exception(e)
                
                return False
            
            return finalname

    def _endReadout(self):
        
        if not self.drv.endReadout(self.ccd):
            err = self.drv.getError()
            logging.error("Error ending readout: %d %s" % err)
            return False
        
        # fire exposeComplete event
        self.readoutComplete()
        
        return True
