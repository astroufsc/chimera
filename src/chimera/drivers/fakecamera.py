#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

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

import time
import random
import threading
import sys
import urllib
import gzip
import os
import logging

import numpy as N
import pyfits

from chimera.interfaces.cameradriver      import ICameraDriver
from chimera.interfaces.filterwheeldriver import IFilterWheelDriver
from chimera.interfaces.camera            import Shutter

from chimera.core.chimeraobject      import ChimeraObject
from chimera.core.exceptions         import ChimeraException, ObjectNotFoundException

from chimera.util.imagesave import ImageSave

from chimera.core.lock import lock

from chimera.core.log import setConsoleLevel
setConsoleLevel(logging.DEBUG)


class FakeCamera (ChimeraObject, ICameraDriver, IFilterWheelDriver):

    __config__ = {"telescope"   : "/Telescope/0",
                  "dome"        : "/Dome/0",
                  "ccd_width"   : 1530,
                  "ccd_height"  : 1020,
                  "use_dss"     : False}
    
    def __init__ (self):
        ChimeraObject.__init__(self)

        self.__exposing = False
        self.__cooling  = False

        self.__abort = threading.Event()
        self.__lastFilter = 0
        self.__temperature = 20.0
        self.__lastFrameStart = 0

    def __start__ (self):
        self.setHz(2)

    def open(self, device):
        return True

    def close(self):
        return True

    def control (self):
        if self.isCooling():
            self.__temperature -= 1.5
            
        return True

    def ping(self):
        return True

    def isExposing(self):
        return self.__exposing

    @lock
    def expose(self):
        self.__exposing = True
        self.__abort.clear()

        ret = ()

        # normal exposure
        if self._expose():
            ret = self._readout()

        self.__exposing = False
        return ret

    def _expose(self):
        
        self.exposeBegin(self["exp_time"])

        t=0
        self.__lastFrameStart = time.time()
        while t < self["exp_time"]:
            if self.__abort.isSet():
                return self["readout_aborted"]
            
            time.sleep (0.1)            
            t+=0.1

        self.exposeComplete()
        return True
    
    def eps_equal(a, b, eps=0.01):
        return abs(a-b) <= eps

    def gunzip(self, file, newext):
        r_file = gzip.GzipFile(file, 'r')
        write_file = file + '.' + newext
        w_file = open(write_file, 'w')
        w_file.write(r_file.read())
        w_file.close()
        r_file.close()
                
    def make_dark(self, shape, dtype):
        ret = N.zeros(shape, dtype=dtype)
        normtemp= (10 * 2**((self.__temperature-25)/7)) * self["exp_time"]
        ret += normtemp + N.random.random(shape)  # +/- 1 variance in readout
        return ret

    def make_flat(self, shape, dtype):

        """
        Flat is composition of:
         - a normal distribution of mean=1000, sigma=1
         - plus a pixel sensitivity constant, which is axis dependent
         - plus a bad region with different mean level
        """

        iadd=15.0/shape[0]
        jadd=10.0/shape[1]

        badlevel = 50

        badareai=shape[0]/2
        badareaj=shape[1]/2

        ret  = N.zeros(shape, dtype=dtype)
        ret += N.fromfunction(lambda i,j: random.gauss(1000, 1) + i*jadd - j*jadd, shape)

        ret[badareai:,badareaj:] += badlevel

        return ret
        
    def _readout(self):
        
        pix = None
        telescope = None
        dome = None

        next_filename = ImageSave.save(pix, 
                                       self["directory"],
                                       self["file_format"],
                                       self["file_extension"],
                                       self["date_format"],
                                       self.__lastFrameStart,
                                       self["exp_time"],                                       
                                       self["bitpix"],
                                       self["save_on_temp"],
                                       dry=True)

        self.readoutBegin(next_filename)

        try:
            telescope = self.getManager().getProxy(self['telescope'], lazy=True)
            dome = self.getManager().getProxy(self['dome'], lazy=True)
        except ObjectNotFoundException:
            self.log.debug("FakeCamera could't found telescope/dome.")


        if (self["shutter"]==Shutter.CLOSE):
            self.log.info("Shutter closed -- making dark")
            pix = self.make_dark((self["ccd_height"],self["ccd_width"]), N.float)

        else:

            if telescope and dome:
                # use telescope/dome to get a real image from DSS if slit in right position

                self.log.debug("Dome open? "+ str(dome.isSlitOpen()))

                if dome.isSlitOpen() and self["use_dss"]:
                    domeAZ=dome.getAz().toD()
                    if (domeAZ > 358):
                        domeAZ-=360     #take care of wrap-around
                    telAZ=telescope.getAz().toD()
                    self.log.debug("Dome AZ: "+str(domeAZ)+"  Tel AZ: "+str(telAZ))
                    if (abs(domeAZ-telAZ) <= 3):
                        self.log.debug("Eps equal -- getting DSS")
                        #http://archive.eso.org/dss/dss/image?ra=20+03+43&dec=-08+10+21&equinox=J2000&x=5&y=5&Sky-Survey=DSS1&mime-type=application/x-fits
                        #http://stdatu.stsci.edu/cgi-bin/dss_search?v=quickv&r=13+29+52.37&d=%2B47+11+40.8&e=J2000&h=15&w=15&f=fits&c=gz&fov=NONE&v3=
                        url = "http://stdatu.stsci.edu/cgi-bin/dss_search?v=poss1_red&r=" + \
                              urllib.quote(telescope.getRa().strfcoord().replace(":"," ")) + \
                              "&d=" + urllib.quote(telescope.getDec().strfcoord().replace(":"," ")) + \
                              "&h=29&w=43.5&f=fits&c=gz&fov=NONE&v3="
                        self.log.debug("Attempting URL: "+url)

                    try:
                        dssfile=urllib.urlretrieve(url)[0]
                        self.gunzip(dssfile,'fits')
                        os.remove(dssfile)
                        dssfile+='.fits'
                        hdulist=pyfits.open(dssfile)
                        pix = hdulist[0].data
                        hdulist.close()
                        os.remove(dssfile)
                    except Exception, e:
                        self.log.warning("General error getting DSS image: " + str(e))
                        
                    self.log.debug("Making flat...")
                    try:
                        pix *= (self.make_flat(pix.shape, N.float)/1000)
                    except Exception, e:
                        self.log.warning("Pix mult error: " + str(e))
                        
                    self.log.debug("Generating dark...")
                    try:
                        pix += self.make_dark(pix.shape, N.float)
                    except Exception, e:
                        self.log.warning("Pix add error: " + str(e))
            else:
                # without telescope/dome, just a flat pattern with dark noise
                try:
                    self.log.info("Making flat image: " + str(self["ccd_height"]) + "x" + str(self["ccd_width"]))
                    self.log.debug("Generating dark...")
                    pix = self.make_dark((self["ccd_height"],self["ccd_width"]), N.float)
                    self.log.debug("Making flat...")
                    pix += self.make_flat((self["ccd_height"],self["ccd_width"]), N.float)
                except Exception, e:
                    self.log.warning("MakekFlat error: " + str(e))


        #Last resort if nothing else could make a picture
        if (pix == None):
            pix = N.zeros((100,100), dtype=N.int32)

        next_filename = ImageSave.save(pix, 
                                       self["directory"],
                                       self["file_format"],
                                       self["file_extension"],
                                       self["date_format"],
                                       self.__lastFrameStart,
                                       self["exp_time"],                                       
                                       self["bitpix"],
                                       self["save_on_temp"])

        self.readoutComplete(next_filename)
        
        return next_filename

    def abortExposure(self):

        if not self.isExposing(): return

        self.__abort.set()

        # busy waiting for exposure/readout stops
        while self.isExposing(): time.sleep(0.1)
            
        self.abortComplete()

    @lock
    def startCooling(self):
        self.__cooling = True
        return True

    @lock
    def stopCooling(self):
        self.__cooling = False
        return True

    def isCooling(self):
        return self.__cooling

    @lock
    def getTemperature(self):
        return self.__temperature + random.random()

    def getFilter (self):
        return self.__lastFilter

    @lock
    def setFilter (self, filter):
        self.filterChange(filter, self.__lastFilter)
        self.__lastFilter = filter
