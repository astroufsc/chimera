from __future__ import division
from math import fabs
import os
import ntpath
import time

from chimera.controllers.imageserver.util import getImageServer
from chimera.util.catalogs.landolt import Landolt
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import (CantPointScopeException, CantSetScopeException, printException, ChimeraException)
from chimera.interfaces.camera import Shutter
from chimera.interfaces.telescope import SlewRate
from chimera.interfaces.pointverify import PointVerify as IPointVerify
from chimera.util.image import ImageUtil, Image
from chimera.util.position import Position
from chimera.util.coord import Coord
from chimera.util.astrometrynet import AstrometryNet, NoSolutionAstrometryNetException


class PointVerify(ChimeraObject, IPointVerify):
    """
    Verifies telescope pointing.
    There are two ways of doing this:
       - verify the field the scope has been pointed to
       - choose a field (from a list of certified fields) and try verification
    """

    # normal constructor
    # initialize the relevant variables
    def __init__(self):
        ChimeraObject.__init__(self)
        self.ntrials = 0  # number times we try to center on a field
        self.nfields = 0  # number of fields we try to center on
        self.checkedpointing = False  # True = Standard field is verified
        self.currentField = 0  # counts fields tried to verify

    def getTel(self):
        return self.getManager().getProxy(self["telescope"])

    def getCam(self):
        return self.getManager().getProxy(self["camera"])

    def getFilterWheel(self):
        return self.getManager().getProxy(self["filterwheel"])

    def _takeImage(self):

        cam = self.getCam()
        if cam["telescope_focal_length"] is None:
            raise ChimeraException("telescope_focal_length parameter must be set on camera instrument configuration")
        if self["filterwheel"] is not None:
            fw = self.getFilterWheel()
            fw.setFilter(self["filter"])
        frames = cam.expose(exptime=self["exptime"], frames=1, shutter=Shutter.OPEN, filename="pointverify-$DATE")

        if frames:
            image = frames[0]
            image_path = image.filename()
            if not os.path.exists(image_path):  # If image is on a remote server, donwload it.

                #  If remote is windows, image_path will be c:\...\image.fits, so use ntpath instead of os.path.
                if ':\\' in image_path:
                    modpath = ntpath
                else:
                    modpath = os.path
                image_path = ImageUtil.makeFilename(os.path.join(getImageServer(self.getManager()).defaultNightDir(),
                                                                 modpath.basename(image_path)))
                t0 = time.time()
                self.log.debug('Downloading image from server to %s' % image_path)
                if not ImageUtil.download(image, image_path):
                    raise ChimeraException('Error downloading image %s from %s' % (image_path, image.http()))
                self.log.debug('Finished download. Took %3.2f seconds' % (time.time() - t0))
            return image_path, image
        else:
            raise Exception("Could not take an image")

    def pointVerify(self):
        """
        Checks telescope pointing.
        If abs ( telescope coordinates - image coordinates ) > tolerance
           move the scope
           take a new image
           test again
           do this while ntrials < max_trials

        Returns True if centering was succesful
                False if not
        """

        # take an image and read its coordinates off the header

        try:
            image_path, image = self._takeImage()
            self.log.debug("Taking image: image name %s" % image_path)
        except:
            self.log.error("Can't take image")
            raise

        ra_img_center = image["CRVAL1"]  # expects to see this in image
        dec_img_center = image["CRVAL2"]
        currentImageCenter = Position.fromRaDec(Coord.fromD(ra_img_center),
                                                Coord.fromD(dec_img_center))

        tel = self.getTel()
        # analyze the previous image using
        # AstrometryNet defined in util
        try:
            wcs_name = AstrometryNet.solveField(image_path, findstarmethod="sex")
        except NoSolutionAstrometryNetException, e:
            raise e
            # why can't I select this exception?
            #
            # there was no solution to this field.
            # send the telescope back to checkPointing
            # if that fails, clouds or telescope problem
            # an exception will be raised there
            # self.log.error("No WCS solution")
            # if not self.checkedpointing:
            #    self.nfields += 1
            #    self.currentField += 1
            #    if self.nfields <= self["max_fields"] and self.checkPointing() == True:
            #        self.checkedpointing = True
            #        tel.slewToRaDec(currentImageCenter)
            #        try:
            #            self.pointVerify()
            #            return True
            #        except CanSetScopeButNotThisField:
            #            raise
            #
            #    else:
            #        self.checkedpointing = False
            #        self.currentField = 0
            #        raise Exception("max fields")
            #
            # else:
            #    self.checkedpointing = False
            #    raise CanSetScopeButNotThisField("Able to set scope, but unable to verify this field %s" %(currentImageCenter))
        wcs_image = Image.fromFile(wcs_name)
        ra_wcs_center, dec_wcs_center = wcs_image.worldAt((image["NAXIS1"]/2., image["NAXIS2"]/2.))
        currentWCS = Position.fromRaDec(Coord.fromD(ra_wcs_center), Coord.fromD(dec_wcs_center))

        # save the position of first trial:
        if self.ntrials == 0:
            initialPosition = Position.fromRaDec(
                Coord.fromD(ra_img_center), Coord.fromD(dec_img_center))

        # write down the two positions for later use in mount models
        if self.ntrials == 0:
            site = self.getManager().getProxy("/Site/0")
            logstr = "Pointing Info for Mount Model: %s %s %s %s %s" % (site.LST(), site.MJD(), image["DATE-OBS"],
                                                                        initialPosition, currentWCS)
            self.log.info(logstr)

        delta_ra = ra_img_center - ra_wcs_center
        delta_dec = dec_img_center - dec_wcs_center

        # *** need to do real logging here
        logstr = "%s ra_tel = %f dec_tel = %f ra_img = %f dec_img = %f delta_ra = %f delta_dec = %f" % (
        image["DATE-OBS"], ra_img_center, dec_img_center, ra_wcs_center, dec_wcs_center, delta_ra, delta_dec)
        self.log.debug(logstr)

        if (fabs(delta_ra) > self["tolra"]) or (fabs(delta_dec) > self["toldec"]):
            self.log.debug("Telescope not there yet. Trying again")
            self.ntrials += 1
            if (self.ntrials > self["max_trials"]):
                self.ntrials = 0
                raise CantPointScopeException(
                    "Scope does not point with a precision of %f (RA) or %f (DEC) after %d trials\n" % (
                        self["tolra"], self["toldec"], self["max_trials"]))
            time.sleep(5)
            tel.moveOffset(Coord.fromD(delta_ra), Coord.fromD(delta_dec), rate=SlewRate.CENTER)
            self.pointVerify()
        else:
            # if we got here, we were succesfull, reset trials counter
            self.ntrials = 0
            self.currentField = 0
            # and save final position
            # write down the two positions for later use in mount models
            logstr = "Pointing: final solution %s %s %s" % (image["DATE-OBS"],
                                                            currentImageCenter,
                                                            currentWCS)
            # self.log.debug("Synchronizing telescope on %s" % currentWCS)
            # tel.syncRaDec(currentWCS)

            # *** should we sync the scope ???
            # maybe there should be an option of syncing or not
            # the first pointing in the night should sync I believe
            # subsequent pointings should not.
            # another idea is to sync if the delta_coords at first trial were
            # larger than some value
            self.log.info(logstr)

        return True

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
        site = self.getManager().getProxy("/Site/0")
        lst = site.LST()
        lat = site["latitude"]
        coords = Position.fromRaDec(lst, lat)

        self.log.info("Check pointing - Zenith coordinates: %f %f" % (lst, lat))

        tel = self.getTel()

        # use the Vizier catalogs to see what Landolt field is closest to
        # zenith
        self.log.debug("Calling landolt")
        fld = Landolt()
        fld.useTarget(coords, radius=45)
        obj = fld.find(limit=self["max_fields"])

        self.log.debug("Objects returned from Landolt: %s" % obj)
        # get ra, dec to call pointVerify
        ra = obj[self.currentField]["RA"]
        dec = obj[self.currentField]["DEC"]
        name = obj[self.currentField]["ID"]
        self.log.debug("Current object: %s, %s, %s", ra, dec, name)

        self.log.info("Chose %s %f %f" % (name, ra, dec))
        tel.slewToRaDec(Position.fromRaDec(ra, dec))
        try:
            self.pointVerify()
        except Exception, e:
            printException(e)
            raise CantSetScopeException(
                "Can't set scope on field %s %f %f we are in trouble, call for help" %
                (name, ra, dec))
        return True

    def findStandards(self):
        """
        Not yet implemented.
        The idea is to find the best standard field to do automatic setting of
        the telescope coordinates.
        It seems that for telescopes > 40cm Landolt fields suffice.
        For scopes < 40 cm on bright skies we may need to build a list of
        compact open clusters.
        """
        site = self.getManager().getProxy("/Site/0")
        lst = site.LST()
        # *** need to come from config file
        min_mag = 6.0
        max_mag = 11.0
        self.searchStandards(lst - 3, lst + 3, min_mag, max_mag)

    def searchStandards(self, min_ra, max_ra, min_mag, max_mag):
        """
        Searches a catalog of standards for good standards to use
        They should be good for focusing, pointing and extinction

        @param min_ra: minimum RA of observable standard
        @type  min_ra: L{float}

        @param max_ra: maximum RA of observable standard
        @type  max_ra: L{float}

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
