from __future__ import division

from chimera.util.catalogs.landolt import Landolt
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException

from chimera.interfaces.camera import Shutter
from chimera.util.position import Position
from chimera.util.coord import Coord
from chimera.util.image import Image

from chimera.util.astrometrynet import AstrometryNet, NoSolutionAstrometryNetException


class CantPointScopeException(ChimeraException):
    """
    This exception is raised when we cannot center the scope on a field
    It may happen if there is something funny with our fields like:
    faint objects, bright objects, extended objects
    or non-astronomical problems like:
    clouds, mount misalignment, dust cover, etc
    When this happens one can simply go on and observe or ask for a checkPoint
    if checkPoint succeeds then the problem is astronomical
    if checkPoint fails then the problem is non-astronomical
    """


class CanSetScopeButNotThisField(ChimeraException):
    pass

class CantSetScopeException(ChimeraException):
    """
    This exception is raised to indicate we could not set the telescope 
    coordinates when trying to do it on a chosen field.  
    Chosen fields are those known to work for setting the scope.
    So, if it fails we must have some serious problem.
    Might be clouds, might be mount misalignment, dust cover, etc, etc
    Never raise this exception for a science field.  It may be that pointverify 
    fails there because of bright objects or other more astronomical reasons
    """
    
class PointVerify (ChimeraObject):
    """
    If the telescope can't point:

    raise exception CantPointScopeException

    """

    # set of parameters and their defaults
    __config__ = {"telescope"          : "/Telescope/0",
                  "camera"             : "/Camera/0",
                  "filterwheel"        : "/FilterWheel/0",
                  "tolra"              : 0.0166666666667,
                  "toldec"             : 0.0166666666667,
                  "exptime"            :  10.0,
                  "filter"             :  "R",
                  "max_trials"         :  10

                  }

    # normal constructor
    # initialize the relevant variables
    def __init__ (self):
        ChimeraObject.__init__ (self)
        self.ntrials = 0

    #def __start__ (self):
        #self.pointVerify()
        #self.checkPointing()
        #return True
        

    def getTel(self):
        return self.getManager().getProxy(self["telescope"])

    def getCam(self):
        return self.getManager().getProxy(self["camera"])

    def getFilter(self):
        return self.getManager().getProxy(self["filterwheel"])

    def _takeImage (self):

        cam = self.getCam()
        #filename = time.strftime("pointverify-%Y%m%d%H%M%S")
        frame = cam.expose(exp_time=self["exptime"],
                           frames=1, shutter=Shutter.OPEN,
                           filename="pointverify-$DATE")
        #                   filename=filename)
 
        if frame:
            imageserver = self.getManager().getProxy(frame[0])
            img = imageserver.getProxyByURI(frame[0])
            return("/media/USB2/astindices/demo/dss/NH1_a10d30.fits")
            #return img.getPath()

        else:
            raise Exception("Could not take an image")
        

    def pointVerify (self):
        """ Checks telescope pointing

        Checks the pointing.
        If telescope coordinates - image coordinates > tolerance
           move the scope
           take a new image
           test again
           do this while ntrials < max_trials

        Returns True if centering was succesful
                False if not
        """

        # take an image and read its coordinates off the header
        try:
            image_name = self._takeImage()
            # for testing purposes uncomment line below and specify some image
        except:
            self.log.error( "Can't take image" )
            raise
            
        image = Image.fromFile(image_name) # Image defined in util
        ra_img_center = image["CRVAL1"]    # expects to see this in image
        dec_img_center= image["CRVAL2"]
        currentImageCenter = Position.fromRaDec(Coord.fromD(ra_img_center), 
                                                Coord.fromD(dec_img_center))  

        tel = self.getTel()

        # analyze the previous image using
        # AstrometryNet defined in util
        try:
            wcs_name = AstrometryNet.solveField(image.filename,findstarmethod="sex") 
        except (NoSolutionAstrometryNetException): 
            # why can't I select this exception?
            # 
            # there was no solution to this field.
            # send the telescope back to checkPointing
            # if that fails, clouds or telescope problem
            # an exception will be raised there
            self.log.error("No WCS solution")
            if not self.checkedpointing:
                if self.checkPointing() == True:
                    self.checkedpointing = True
                    tel.slewToRaDec(currentImageCenter)
                    try:
                        self.pointVerify()
                        return True
                    except CanSetScopeButNotThisField:
                        pass # let the caller decide whether we go to next 
                             # field or stay on this with no verification
            else:
                self.checkedpointing = False
                raise CanSetScopeButNotThisField("Able to set scope, but unable to verify this field %s" %(currentImageCenter))



        wcs = Image.fromFile(wcs_name)
        ra_wcs_center = wcs["CRVAL1"] + (wcs["NAXIS1"]/2.0 - wcs["CRPIX1"]) * wcs["CD1_1"]
        dec_wcs_center= wcs["CRVAL2"] + (wcs["NAXIS2"]/2.0 - wcs["CRPIX2"]) * wcs["CD2_2"]
        currentWCS = Position.fromRaDec(Coord.fromD(ra_wcs_center), 
                                        Coord.fromD(dec_wcs_center))  

        # save the position of first trial:
        if (self.ntrials == 0):
            initialPosition = Position.fromRaDec(Coord.fromD(ra_img_center),Coord.fromD(dec_img_center))
            initialWCS = Position.fromRaDec(currentWCS.ra,currentWCS.dec)

        # write down the two positions for later use in mount models
        if ( self.ntrials == 0 ):
            logstr = "Pointing Info for Mount Model: %s %s %s" %(image["DATE-OBS"], initialPosition, currentWCS)
            self.log.info(logstr)
        
        delta_ra = ra_img_center - ra_wcs_center
        delta_dec = dec_img_center - dec_wcs_center

        self.log.debug("%s %s" %(delta_ra, delta_dec))
        self.log.debug("%s %s" %(ra_img_center, ra_wcs_center))
        self.log.debug("%s %s" %(dec_img_center, dec_wcs_center))
        
        # *** need to do real logging here
        logstr = "%s %f %f %f %f %f %f" %(image["DATE-OBS"],ra_img_center,dec_img_center,ra_wcs_center,dec_wcs_center,delta_ra,delta_dec)
        self.log.debug(logstr)



        if ( delta_ra > self["tolra"] ) or ( delta_dec > self["toldec"]):
            print "Telescope not there yet."
            print "Trying again"
            self.ntrials += 1
            if (self.ntrials > self["max_trials"]):
                self.ntrials = 0
                raise CantPointScopeException("Scope does not point with a precision of %f (RA) or %f (DEC) after %d trials\n" % self["tolra"] % self["toldec"] % self["max_trials"])
            tel.moveOffset(delta_ra, delta_dec)
            self.pointVerify()
        else:
            # if we got here, we were succesfull reset trials counter
            self.ntrials = 0
            # and save final position
            # write down the two positions for later use in mount models
            logstr = "Pointing: final solution %s %s %s" %(image["DATE-OBS"],
                                                           currentImageCenter,
                                                           currentWCS)
            self.log.info(logstr)

        return(True)


    def checkPointing(self):
        """
        This method *chooses* a field to verify the telescope pointing.
        Then it does the pointing and verifies it.
        If unsuccesfull e-mail the operator for help
        isto em portugues eh chamado calagem

        Choice is based on some catalog (Landolt here)
        We choose the field closest to zenith
        """
        # find where the zenith is
        site =  self.getManager().getProxy("/Site/0")
        lst = site.LST()
        lat = site["latitude"]
        coords = Position.fromRaDec(lst,lat)

        self.log.info("Check pointing - Zenith coordinates: %f %f" %(lst, lat))

        tel = self.getTel()

        # use the Vizier catalogs to see what Landolt field is closest to zenith
        fld = Landolt()
        fld.useTarget(coords,radius=45)
        obj = fld.find(limit=1)

        # get ra, dec to call pointVerify
        ra = obj[0]["RA"]
        dec = obj[0]["DEC"]
        name = obj[0]["ID"]
        self.log.info("Chose %s %f %f" %(name, ra, dec))
        tel.slewToRaDec(Position.fromRaDec(ra,dec))
        try:
            self.pointVerify()
        except:
            raise CantSetScopeException("Can't set scope on field %s %f %f we are in trouble, call for help" %(name, ra, dec))
        return True
            


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

if __name__ == "__main__":
    
    x = PointVerify()
    # x.checkPointing()
    x.pointVerify()

    
