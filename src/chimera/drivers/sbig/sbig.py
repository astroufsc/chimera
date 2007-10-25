#! /usr/bin/python
# -*- coding: iso8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import time
import logging
import pwd
import threading
import string
import random
import tempfile


# ask to use numpy
os.environ["NUMERIX"] = "numpy"
import pyfits
        
from sbigdrv import *

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.camera import ICameraDriver
from chimera.interfaces.filterwheel import IFilterWheelDriver

from chimera.controllers.blocks import next_seq
        
class SBIG(BasicLifeCycle, ICameraDriver, IFilterWheelDriver):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.drv = SBIGDrv()
        self.ccd = SBIGDrv.imaging

        self.lastTemp = 0
        self.lastFilter = None

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
                        
        return self.open(self.dev)

    def shutdown(self):
        self.close ()

    def control(self):

        temp = self.drv.getTemperature ()

        if temp:

            newTemp = temp[3]

            if (newTemp - self.lastTemp) >= self.config.temp_delta:
                self.temperatureChanged (newTemp, self.lastTemp)
                self.lastTemp = newTemp
        else:
            logging.debug ("Couldn't get CCD temperature (%d %s)" % self.drv.getError ())

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

        return True
        
    def close(self):
        self.drv.closeDevice()
        self.drv.closeDriver()

    def ping(self):
        return self.drv.isLinked()

    def isExposing(self):
        return self.drv.exposing(self.ccd)

    def expose(self, config):

        self.config += config

        if self.isExposing():
            logging.error ("There is another exposure been taken.")
            return False
        
        self.term.clear()

        if self._expose():
            return self._readout()
        else:
            return False

    def abortExposure(self, config):

        self.config += config

        if not self.isExposing():
            logging.debug("There are no exposition in course... abort cancelled.")
            return False
                
        self.term.set()

        logging.debug("Aborting exposure...")

        while self.isExposing():
            time.sleep (0.1)

        return True

    # methods
    def setTemperature(self, config):

        self.config += config

        if not self.drv.setTemperature (self.config.temp_regulation,
                                        self.config.temp_setpoint,
                                        self.config.auto_freeze):
            logging.error("Couldn't set temperature.")
            return False

        return True

    def getTemperature(self):

        ret = self.drv.getTemperature ()

        if not ret:
            logging.error("Couldn't get temperature.")
            return False

        return ret

    def getFilter (self):
        return self.drv.getFilterPosition ()

    def setFilter (self, _filter):

        try:
            position = eval ('self.drv.filter_%d' % _filter)
        except NameError:
            logging.error ("Selected filter not defined on SBIG driver.")
            return False

        ret = self.drv.setFilterPosition (position)

        if not ret:
            logging.error ("Error while changing filter (%d %s)." % self.drv.getError ())
            return False

        # first filter change, so last equals new
        if not self.lastFilter:
            self.lastFilter = _filter

        self.filterChanged (_filter, self.lastFilter)
        self.lastFilter = _filter

        return True
        
    def getFilterStatus (self):
        return self.drv.getFilterStatus ()

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

        while self.isExposing():
                                        
            # check if user asked to abort
            if self.term.isSet():
                # ok, abort and check if user asked to do a readout anyway

                if self.isExposing():
                    self._endExposure()
                
                if self.config.readout_aborted:
                    self._readout()
                    
                return False

        # end exposure and returns
        return self._endExposure()

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
        ret = self._saveFITS(img)
                
        return ret

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
                                "and save_on_temp was not active, the current "
                                "exposure will be lost." % (dest))
                
                return False

            else:
                logging.warning("The direcotry specified (%s) doesn't exist. "
                                "save_on_temp is active, the current exposure will be saved on /tmp" % (dest))

                dest = tempfile.gettempdir ()
                       
        # permission
        if not os.access(dest, os.W_OK):
            # user doesn't have permission to write on dest, check config to know what to do
            uid = os.getuid()
            user = pwd.getpwuid(uid)[0]

            if not self.config.save_on_temp:
                logging.warning("User %s (%d) doesn't have permission to write "
                                "on %s and save_on_temp was not active, the current "
                                "exposure will be lost." % (user, uid, dest))
                
                return False
            else:
                logging.warning("User %s (%d) doesn't have permission to write on %s. "
                                "save_on_temp is active, the current exposure will be saved on /tmp" % (user, uid, dest))
                dest = tempfile.gettempdir ()


        # create filename
        # FIXME: UTC or not UTC?
        date = time.strftime(self.config.date_format, time.gmtime(self.config.start_time))
        
        subs_dict = {'observer': self.config.observer,
                     'date': date,
                     'objname': self.config.obj_name}

        filename = string.Template(self.config.file_format).safe_substitute(subs_dict)

        seq_num = next_seq(dest, filename, self.config.file_extension)

        finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, seq_num, os.path.extsep, self.config.file_extension))

        # check if the finalname doesn't exist
        if os.path.exists(finalname):
            tmp = finalname
            finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, int (random.random()*1000),
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
            logging.error("An error ocurred trying to save on %s. "
                          "The current image will be lost. "
                          "Exception follow" %  finalname)
            
            logging.exception(e)
                
            return False
            
        return finalname

    def _endReadout(self):
        
        if not self.drv.endReadout(self.ccd):
            err = self.drv.getError()
            logging.error("Error ending readout: %d %s" % err)
            return False
        
        # fire readoutComplete event
        self.readoutComplete()
        
        return True
