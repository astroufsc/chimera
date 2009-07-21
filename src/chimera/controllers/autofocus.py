
from __future__ import division

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.core.event import event
from chimera.core.exceptions import ChimeraException, ClassLoaderException
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.interfaces.autofocus import Autofocus as IAutofocus
from chimera.interfaces.autofocus import StarNotFoundException, FocusNotFoundException
from chimera.interfaces.focuser import InvalidFocusPositionException

from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.controllers.imageserver.util         import getImageServer

from chimera.util.image import Image
from chimera.util.output import red, green

import numpy as N
import yaml

plot = True
try:
    import pylab as P
except (ImportError, RuntimeError, ClassLoaderException):
    plot = False

from math import sqrt, ceil
import time
import os
import logging


class FocusFit (object):

    def __init__ (self):

        # input
        self.temperature = None
        self.position = None
        self.fwhm = None
        self.minmax = None

        # calculated
        self.A = 0
        self.B = 0
        self.C = 0

        self.fwhm_fit = None
        self.err = 1e20

    best_focus = property(lambda self: (-self.B / (2*self.A),
                                       (-self.B**2 + 4*self.A*self.C) / (4*self.A)))
 
    def plot (self, filename):
        
        global plot
        
        if plot:
            P.plot(self.position, self.fwhm, "ro", label="data")
            P.plot(self.position, self.fwhm_fit, "b--", label="fit")
            P.plot([self.best_focus[0]], [self.best_focus[1]], "bD", label="best focus from fit")
            
            if self.minmax:
                P.ylim(*self.minmax)
                
            P.title("Focus")
            P.xlabel("Focus position")
            P.ylabel("FWHM (pixel)")
            P.savefig(filename)

    def log (self, filename):
        
        log = open(filename, "w")

        print >> log, "#", time.strftime("%c")
        print >> log, "# A=%f B=%f C=%f" % tuple(self)
        print >> log, "# best focus position: %.3f (FWHM %.3f)" % self.best_focus
        if self.minmax:
            print >> log, "# minmax filtering: %s" % str(self.minmax)

        if self.temperature:
            print >> log, "# focuser temperature: %.3f" % self.temperature

        for position, fwhm in zip(self.position, self.fwhm):
            print >> log, position, fwhm

        log.close()

    def __iter__ (self):
        return (self.A, self.B, self.C).__iter__()

    def __cmp__ (self, other):
        if isinstance(other, FocusFit):
            return (self.err - other.err)
        else:
            return (self.err - other)

    def __hash__ (self):
        return hash((self.A, self.B, self.C, self.err))

    def __nonzero__ (self):
        return (self.position != None) and (self.fwhm != None)

    @staticmethod
    def fit (position, fwhm, temperature=None, minmax=None):

        if minmax and len(minmax) >= 2:
            idxs = (fwhm >= minmax[0]) & (fwhm <= minmax[1])
            position = position[idxs]
            fwhm = fwhm[idxs]

        A, B, C = N.polyfit(position, fwhm, 2)

        fwhm_fit = N.polyval([A,B,C], position)
        
        err = sqrt(sum((fwhm_fit - fwhm)**2) / len(position))

        fit = FocusFit()
        fit.position = position
        fit.fwhm = fwhm
        fit.temperature = temperature
        fit.minmax = minmax

        fit.A, fit.B, fit.C = A,B,C
        fit.err = err
        fit.fwhm_fit = fwhm_fit

        return fit
    
class Autofocus (ChimeraObject, IAutofocus):
    
    """
    Auto focuser
    ============

    This instrument will try to characterizes the current system and
    fit a parabola to a curve made of a star FWHM versus focus
    positions.

    1) take exposure to find focus star.

    2) set window and binning if necessary and start iteration:

       Get n points starting at min_pos and ending at max_pos focus positions,
       and for each position measure FWHM of a target star (currently the
       brighter star in the field).

       Fit a parabola to the FWHM points measured.

    3) Leave focuser at best focus point (parabola vertice)

    """

    def __init__ (self):
        ChimeraObject.__init__ (self)

        self.imageRequest = None
        self.filter = None
        
        self.currentRun = None

        self.best_fit = None

        self._debugging = False
        self._debug_images = []
        self._debug_image = 0

        self._log_handler = None

    @event
    def stepComplete (self, position, star, frame):
        """Raised after every step in the focus sequence with
        information about the last step.
        """

    def getCam(self):
        return self.getManager().getProxy(self["camera"])

    def getFilter(self):
        return self.getManager().getProxy(self["filterwheel"])

    def getFocuser(self):
        return self.getManager().getProxy(self["focuser"])

    def _getID(self):
        return "autofocus-%s" % time.strftime("%Y%m%d-%H%M%S")

    def _openLogger(self):

        if self._log_handler:
            self._closeLogger()
            
        self._log_handler = logging.FileHandler(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun, "autofocus.log"))
        self._log_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
        self._log_handler.setLevel(logging.DEBUG)
        self.log.addHandler(self._log_handler)

    def _closeLogger(self):
        if self._log_handler:
            self.log.removeHandler(self._log_handler)
            self._log_handler.close()

    @lock
    def focus (self, filter=None, exptime=None, binning=None, window=None,
               start=2000, end=6000, step=500,
               minmax=None, debug=False):

        self._debugging = debug

        self.currentRun = self._getID()

        if not os.path.exists(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun)):
            os.mkdir(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun))

        self._openLogger()

        if debug:
            debug_file = open(os.path.join(debug, "autofocus.debug"), "r")
            debug_data = yaml.load(debug_file.read())

            start = debug_data["start"]
            end   = debug_data["end"]
            step  = debug_data["step"]
            
            debug_file.close()

        positions = N.arange(start, end+1, step)

        if not debug:
            # save parameter to ease a debug run later
            debug_data = dict(id=self.currentRun, start=start, end=end, step=step)
            try:
                debug_file = open(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun, "autofocus.debug"), "w")
                debug_file.write(yaml.dump(debug_data))
                debug_file.close()
            except IOError:
                self.log.warning("Cannot save debug information. Debug will be a little harder later.")

        self.log.debug("="*40)
        self.log.debug("[%s] Starting autofocus run." % time.strftime("%c"))
        self.log.debug("="*40)        
        self.log.debug("Focus range: start=%d end=%d step=%d points=%d" % (start, end, step, len(positions)))
        
        # images for debug mode
        if debug:
            self._debug_images = [ "%s/focus-%04d.fits" % (debug, i)
                                   for i in range(1, len(positions)+2)]

        self.imageRequest = ImageRequest()
        self.imageRequest["exp_time"] = exptime or 10
        self.imageRequest["frames"] = 1
        self.imageRequest["shutter"] = "OPEN"
        
        if filter:
            self.filter = filter
            self.log.debug("Using filter %s." % self.filter)
        else:
            self.filter = False
            self.log.debug("Using current filter.")

        if binning:
            self.imageRequest["binning"] = binning

        if window:
            self.imageRequest["window"] = window
        
        # 1. Find best star to focus on this field

        star_found = self._findBestStarToFocus(self._takeImageAndResolveStars())

        if not star_found:

            tries = 0

            while not star_found and tries < self["max_tries"]:
                star_found = self._findBestStarToFocus(self._takeImageAndResolveStars())
                tries += 1
                
            if not star_found:
                raise StarNotFoundException("Couldn't find a suitable star to focus on. "
                                            "Giving up after %d tries." % tries)

        try:
            fit = self._fitFocus(positions, minmax)

            if not self.best_fit or fit < self.best_fit:
                self.best_fit = fit
                
            return (self.currentRun, fit.A, fit.B, fit.C, fit.best_focus)

        finally:
            # reset debug counter
            self._debug_image = 0

    def _fitFocus (self, positions, minmax=None):
        
        focuser = self.getFocuser()
        initial_position = focuser.getPosition()

        self.log.debug("Initial focus position: %04d" % initial_position)

        fwhm  = N.zeros(len(positions))

        for i, position in enumerate(positions):

            self.log.debug("Moving focuser to %d" % int(position))

            focuser.moveTo(position)

            frame = self._takeImage()
            stars = self._findStars(frame)
            star = self._findBrighterStar(stars)

            star["CHIMERA_FLAGS"] = green("OK")

            if abs(star["FWHM_IMAGE"] - 4.18) <= 0.02:
                self.log.debug("Ignoring star at (X,Y)=(%d,%d) FWHM magic number=%.3f, FLUX=%.3f" % (star["XWIN_IMAGE"], star["YWIN_IMAGE"],
                                                                                                     star["FWHM_IMAGE"], star["FLUX_BEST"]))
                star["CHIMERA_FLAGS"] = red("Ignoring, SExtractor FWHM magic number.")
            elif minmax[0] <= star["FWHM_IMAGE"] <= minmax[1]:
                self.log.debug("Ignoring star at (X,Y)=(%d,%d) FWHM magic number=%.3f, FLUX=%.3f" % (star["XWIN_IMAGE"], star["YWIN_IMAGE"],
                                                                                                     star["FWHM_IMAGE"], star["FLUX_BEST"]))
                star["CHIMERA_FLAGS"] = red("Ignoring, FWHM above/below minmax limits.")
            else:
                self.log.debug("Adding star to curve. (X,Y)=(%d,%d) FWHM=%.3f FLUX=%.3f" % (star["XWIN_IMAGE"], star["YWIN_IMAGE"],
                                                                                            star["FWHM_IMAGE"], star["FLUX_BEST"]))
                fwhm[i] = star["FWHM_IMAGE"]
                
            self.stepComplete(position, star, frame)

        # fit a parabola to the points and save parameters
        try:
            if minmax:
                self.log.debug("Minmax filtering FWHM (%.3f,%.3f)" % minmax)
            fit = FocusFit.fit(positions, fwhm, minmax=minmax)
        except Exception, e:
            focuser.moveTo(initial_position)

            raise FocusNotFoundException("Error trying to fit a focus curve. "
                                         "Leaving focuser at %04d" % initial_position)
            

        fit.plot(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun, "autofocus.plot.png"))
        fit.log(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun, "autofocus.plot.dat"))

        # leave focuser at best position
        try:
            if N.isnan(fit.best_focus[0]):
                raise FocusNotFoundException("Focus fitting error: fitting do not converges (NaN result). See logs for more info.")
            
            focuser.moveTo(int(fit.best_focus[0]))
            self.log.debug("Best focus position: %.3f" % fit.best_focus[0])
        except InvalidFocusPositionException:
            self.log.debug("Coundt' find best focus position. Check logs.")

        return fit
    
    def _takeImageAndResolveStars (self):

        frame = self._takeImage()
        stars = self._findStars(frame)

        return stars

    def _takeImage (self):

        if self._debugging:
            try:
                frame = self._debug_images[self._debug_image]
                self._debug_image += 1

                img = Image.fromFile(frame)
                srv = getImageServer(self.getManager())
                return srv.register(img)
            except IndexError:
                raise ChimeraException("Cannot find debug images")

        self.imageRequest["filename"] = os.path.join(SYSTEM_CONFIG_DIRECTORY, self.currentRun, "focus.fits")

        cam = self.getCam()
        
        if self.filter:
            filter = self.getFilter()
            filter.setFilter(self.filter)
            
        frame = cam.expose(self.imageRequest)

        if frame:
            return frame[0]
        else:
            raise Exception("Error taking image.")

    def _findStars (self, frame):

        config = {}
        config['PIXEL_SCALE'] = 0 # use WCS info
        config['BACK_TYPE']   = "AUTO"

        config['SATUR_LEVEL'] = self.getCam()["ccd_saturation_level"]

        # improve speed with higher threshold
        config['DETECT_THRESH'] = 3.0

        # no output, please
        config['VERBOSE_TYPE'] = "QUIET"

        # our "star" dict entry will contain all this members
        config['PARAMETERS_LIST'] = ["NUMBER",
                                     "XWIN_IMAGE", "YWIN_IMAGE",
                                     "FLUX_BEST", "FWHM_IMAGE",
                                     "FLAGS"]

        catalogName = os.path.splitext(frame.filename())[0] + ".catalog"
        configName = os.path.splitext(frame.filename())[0] + ".config"
        return frame.extract(config, saveCatalog=catalogName, saveConfig=configName)

    def _findBestStarToFocus (self, catalog):

        # simple plan: brighter star
        # FIXME: avoid "border" stars
        return self._findBrighterStar(catalog)

    def _findBrighterStar (self, catalog):

        fluxes = [star for star in catalog if star["FLAGS"] == 0]

        if not fluxes: # empty catalog
            return False

        return max(fluxes, key=lambda star: star["FLUX_BEST"])
        

if __name__ == "__main__":
    
    x = Autofocus()
    # x.checkPointing()
    x._takeImage()
