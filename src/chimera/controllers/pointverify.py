
from __future__ import division

from chimera.util.catalogs.landolt import Landolt
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.core.exceptions import ChimeraException, printException

from chimera.interfaces.camera import Shutter
from chimera.interfaces.filterwheel import Filter

from chimera.util.enum import Enum

from chimera.util.sextractor import SExtractor
from chimera.util.position import Position
from chimera.util.image import Image

from chimera.util.astrometrynet import AstrometryNet
#from chimera.util.ephemerides import Standards

import numpy as N
import pylab as P

import tempfile
import time
from math import sqrt

    
class PointVerify (ChimeraObject):
    """
    If the telescope can't point:

    raise exception CantPointScopeException

    """

    # set of parameters and their defaults
    __config__ = {"telescope"          : "/Telescope/0",
                  "camera"             : "/Camera/0",
                  "filterwheel"        : "/FilterWheel/0" 
                  }

    # normal constructor
    # initialize the relevant variables
    def __init__ (self):
        ChimeraObject.__init__ (self)

        self.exptime = 10
        self.filter  = "B"

        # *** the tolerances must come from the config files
        # for now they are just hardwired
        self.tolra = 1./60.  # pointing tolerance in degrees
        self.toldec = 1./60.

        self.ntrials = 0
        self.max_trials = 10

    def getTel(self):
        return self.getManager().getProxy(self["telescope"])

    def getCam(self):
        return self.getManager().getProxy(self["camera"])

    def getFilter(self):
        return self.getManager().getProxy(self["filterwheel"])

    def _takeImage (self):

        cam = self.getCam()
        
        frame = cam.expose(exp_time=self.exptime,
                           frames=1, shutter=Shutter.OPEN,
                           filename=filename)
        return frame[0]

        if frame:
            imageserver = self.getManager().getProxy(frame[0])
            img = imageserver.getProxyByURI(frame[0])
            return img.getPath()

        else:
            raise Exception("Couldn't take an image")
        
        # return("/media/USB2/astindices/demo/dss/NH1_a10d30.fits")

    def pointVerify (self):
        """ Checks telescope pointing

        @param coords: Coordinates the telescope has been pointed to
        @type  coords: L{Position}

        Checks the pointing.
        If telescope coordinates - image coordinates > tolerance
           move the scope
           take a new image
           test again
           do this while ntrials < max_trials
        """

        # take an image and read its coordinates off the header
        image_name = self._takeImage()
        image = Image.fromFile(image_name) # Image defined in util
        ra_img_center = image["CRVAL1"]    # expects to see this in image
        dec_img_center= image["CRVAL2"]

        # analyze the previous image using
        # AstrometryNet defined in util
        wcs_name = AstrometryNet.solveField(image.filename) 
        try:
            wcs = Image.fromFile(wcs_name)
        except:
            print "No WCS solution"
        ra_wcs_center = wcs["CRVAL1"]
        dec_wcs_center= wcs["CRVAL2"]
        
        delta_ra = ra_img_center - ra_wcs_center
        delta_dec = dec_img_center - dec_wcs_center

        print delta_ra, delta_dec
        print ra_img_center, ra_wcs_center
        print dec_img_center, dec_wcs_center
        
        # *** need to do real logging here
        logstr = "%s %f %f %f %f %f %f" %(image["DATE-OBS"],ra_img_center,dec_img_center,ra_wcs_center,dec_wcs_center,delta_ra,delta_dec)
        print logstr

        if ( delta_ra > self.tolra ) or ( delta_dec > self.toldec):
            print "Telescope not there yet."
            print "Trying again"
            self.ntrials += 1
            # *** do I get a telescope everytime? YES, it won't hurt
            # in python the unused objects are discarded at the end
            tel = self.getTel()
            tel.slewToRaDec((coords.ra + delta_ra, 
                             coords.dec + delta_dec))
            if (self.ntrials > self.max_trials):
                self.ntrials = 0
                raise CantPointScopeException("Scope does not point with a precision of %f (RA) or %f (DEC) after %d trials\n" % self.tolra % self.toldec % self.max_trials)
                return(False)
            self.point(tel.getPositionRaDec())
        # if we got here, we were succesfull
        self.ntrials = 0
        return(True)


    def checkPointing(self):
        """
        This method chooses a field to verify the telescope pointing.
        Then it does the pointing and verifies it.
        If unsuccesfull e-mail the operator for help
        isto em portugues eh chamado calagem
        """
        # find where the zenith is
        site =  self.getManager().getProxy("/Site/0")
        lst = site.LST()
        lst = "14:00:00"
        lat = site["latitude"]
        lat = "-22:00:00"
        coords = Position.fromRaDec(lst,lat)

        # use the Vizier catalogs to see what Landolt field is close to zenith
        fld = Landolt()
        fld.useTarget(coords,radius=45)
        obj = fld.find(limit=1)

        # get ra, dec to call pointVerify
        ra = obj[0]["RA"]
        dec = obj[0]["DEC"]
        print ra, dec
        self.pointVerify(Position.fromRaDec(ra,dec))


    def findStandards(self):
        site =  self.getManager().getProxy("/Site/0")
        lst = site.LST()
        # *** need to come from config file
        min_mag = 11.0
        max_mag = 15.0
        self.searchStandards(lst-3,lst+3,min_mag,max_mag)

    def searchStandards(self, max_z, max_ha,min_mag,max_mag):
        """
        Searches a catalog of standards for good standards to use
        They should be good for focusing, pointing and extinction

        @param max_z: maximum zenith distance of observable standard
        @type  max_z: L{float}

        @param max_ha: maximum hour angle of observable standard 
        @type  max_ha: L{float}

        @param min_mag: minimum magnitude of standard
        @type  min_mag: L{float}

        @param max_mag: maximum magnitude of standard
        @type  max_mag: L{float}

        should return a list of standard stars within the limits
        """

class CantPointScopeException(ChimeraException):
    pass


if __name__ == "__main__":
    
    x = PointVerify()
    x.pointVerify()

    
