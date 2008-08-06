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
import urllib
import gzip
import os

import numpy as N
import pyfits

from chimera.interfaces.cameradriver      import ICameraDriver
from chimera.interfaces.filterwheeldriver import IFilterWheelDriver
from chimera.interfaces.camera import Shutter

from chimera.controllers.imageserver.image import Image

from chimera.core.chimeraobject      import ChimeraObject
from chimera.core.exceptions         import ChimeraException, ObjectNotFoundException

#from chimera.util.imagesave import ImageSave

from chimera.core.lock import lock

#from chimera.core.log import setConsoleLevel
#import logging
#setConsoleLevel(logging.DEBUG)


class FakeCamera (ChimeraObject, ICameraDriver, IFilterWheelDriver):

    __config__ = {"telescope"   : "/Telescope/0",
                  "dome"        : "/Dome/0",
                  "ccd_width"   : 765,
                  "ccd_height"  : 510,
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
    def expose(self, imageRequest):
#        self.__exposing = True
#        self.__abort.clear()
#
#        ret = ()
#
#        # normal exposure
#        if self._expose():
#            ret = self._readout()
#
#        self.__exposing = False
#        return ret
        
        self.__exposing = True
        self.__abort.clear()
        
        ret = False

        if self._expose(imageRequest):
            ret = self._readout(imageRequest, aborted=False)
        
        self.__exposing=False
        return ret


    def _expose(self, imageRequest):
        
        self.exposeBegin(imageRequest["exp_time"])

        t=0
        self.__lastFrameStart = time.time()
        while t < imageRequest["exp_time"]:
            if self.__abort.isSet():
                return False
            
            time.sleep (0.1)            
            t+=0.1

        self.exposeComplete()
        return True
    
    @staticmethod
    def eps_equal(a, b, eps=0.01):
        return abs(a-b) <= eps

    def gunzip(self, file, newext):
        r_file = gzip.GzipFile(file, 'r')
        write_file = file + '.' + newext
        w_file = open(write_file, 'w')
        w_file.write(r_file.read())
        w_file.close()
        r_file.close()
                
    def make_dark(self, shape, dtype, exptime):
        ret = N.zeros(shape, dtype=dtype)
        #Taken from specs for KAF-1603ME as found in ST-8XME
        #normtemp is now in ADU/pix/sec
        normtemp= ((10 * 2**((self.__temperature-25)/6.3)) * exptime)/2.3
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

        # this array is only to make sure we create our array with the right dtype
        ret  = N.zeros(shape, dtype=dtype)

        ret += N.random.normal(1000, 1, shape)
        ret += N.fromfunction(lambda i,j: i*jadd - j*jadd, shape)

        ret[badareai:,badareaj:] += badlevel

        return ret
        
    def _readout(self, imageRequest, aborted=False):
        
        pix = None
        telescope = None
        dome = None

#        next_filename = ImageSave.save(pix, 
#                                       self["directory"],
#                                       self["file_format"],
#                                       self["file_extension"],
#                                       self["date_format"],
#                                       self.__lastFrameStart,
#                                       self["exp_time"],                                       
#                                       self["bitpix"],
#                                       self["save_on_temp"],
#                                       dry=True)

        self.readoutBegin(imageRequest)
        
        try:
            telescope = self.getManager().getProxy(self['telescope'], lazy=True)
        except ObjectNotFoundException:
            pass
        try:
            dome = self.getManager().getProxy(self['dome'], lazy=True)
        except ObjectNotFoundException:
            pass
        
        if not (telescope or dome):
            self.log.debug("FakeCamera couldn't find telescope or dome.")
        elif telescope and (not dome):
            self.log.debug("FakeCamera couldn't find dome.")
        elif (not telescope) and dome:
            self.log.debug("FakeCamera couldn't find telescope.")


        if (imageRequest["shutter"]==Shutter.CLOSE):
            self.log.info("Shutter closed -- making dark")
            pix = self.make_dark((self["ccd_height"],self["ccd_width"]), N.float, imageRequest['exp_time'])

        else:

            if telescope and dome:
                # use telescope/dome to get a real image from DSS if slit in right position

                self.log.debug("Dome open? "+ str(dome.isSlitOpen()))

                if dome.isSlitOpen() and self["use_dss"]:
                    domeAZ=dome.getAz().toD()
                    telAZ=telescope.getAz().toD()
                    if (telAZ < 3 and domeAZ > 357):
                    	domeAZ-=360     #take care of wrap-around
                    self.log.debug("Dome AZ: "+str(domeAZ)+"  Tel AZ: "+str(telAZ))
                    if (abs(domeAZ-telAZ) <= 3):
                        self.log.debug("Dome & Slit aligned -- getting DSS")
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
                            self.log.warning("Error generating flat: " + str(e))
                        self.log.debug("Generating dark...")
                        try:
                            pix += self.make_dark(pix.shape, N.float, imageRequest['exp_time'])
                        except Exception, e:
                            self.log.warning("Error generating dark: " + str(e))
            # without telescope/dome, or if dome/telescope aren't aligned, or the dome is closed
            # or we otherwise failed, just make a flat pattern with dark noise
            if (pix == None):
               try:
                   self.log.info("Making simulated flat image: " + str(self["ccd_height"]) + "x" + str(self["ccd_width"]))
                   self.log.debug("Generating dark...")
                   pix = self.make_dark((self["ccd_height"],self["ccd_width"]), N.float, imageRequest['exp_time'])
                   self.log.debug("Making flat...")
                   pix += self.make_flat((self["ccd_height"],self["ccd_width"]), N.float)
               except Exception, e:
                    self.log.warning("MakekFlat error: " + str(e))
        
        #Last resort if nothing else could make a picture
        if (pix == None):
            pix = N.zeros((100,100), dtype=N.int32)

#        next_filename = ImageSave.save(pix, 
#                                       self["directory"],
#                                       self["file_format"],
#                                       self["file_extension"],
#                                       self["date_format"],
#                                       self.__lastFrameStart,
#                                       self["exp_time"],                                       
#                                       self["bitpix"],
#                                       self["save_on_temp"],
#                                       dry=False)
        
        imageRequest.addPostHeaders(self.getManager())
        
        img = Image.imageFromImg(pix, imageRequest, [
                                               ('DATE-OBS',Image.formatDate(self.__lastFrameStart),'Date exposure started'),
                                               ('XBINNING',1,'Readout CCD Binning (x-axis)'),
                                               ('YBINNING',1,'Readout CCD Binning (y-axis)'),
                                               ('XWIN_LFT',0,'Readout window x left position'),
                                               ('XWIN_SZ',pix.shape[1],'Readout window width'),
                                               ('YWIN_TOP',0,'Readout window y top position'),
                                               ('YWIN_SZ',pix.shape[0],'Readout window height'),
                                               ('IMAGETYP',imageRequest['image_type'],'Image type'),
                                               ]
                           )

        self.readoutComplete(imageRequest)
        
        return img

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
