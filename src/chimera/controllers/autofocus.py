
from __future__ import division

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.core.exceptions import ChimeraException, printException

from chimera.interfaces.camera import Shutter, Binning, Window
from chimera.interfaces.filterwheel import Filter

from chimera.util.enum import Enum

from chimera.util.sextractor import SExtractor

import numpy as N

plot = True
try:
    import pylab as P
except ImportError:
    plot = False

import tempfile
import time
from math import sqrt


Target    = Enum("CURRENT", "AUTO", "OBJECT")
Mode      = Enum("FIT", "FOCUS")
Direction = Enum("AUTO", "IN", "OUT")
Metric    = Enum("FWHM")


class StarNotFoundException (ChimeraException):
    pass

class FocusNotFoundException (ChimeraException):
    pass


class FocusFit (object):

    def __init__ (self):

        # input
        self.position = None
        self.fwhm = None

        # calculated
        self.A = 0
        self.B = 0
        self.C = 0

        self.fwhm_fit = None
        self.err = 1e20

        self._best_focus = None

    best_focus = property(lambda self: (-self.B / (2*self.A),
                                       (-self.B**2 + 4*self.A*self.C) / (4*self.A)))
 
    def plot (self, filename):
        
        global plot
        
        if plot:
            P.plot(self.position, self.fwhm, "ro", label="data")
            P.errorbar(self.position, self.fwhm_fit, yerr=self.err, fmt="k:",
                       ms=15, label="fit")
            
            P.plot([self.best_focus[0]], [self.best_focus[1]], "bD",
                   label="best focus from fit")
            
            P.legend()
            P.title("Focus")
            P.xlabel("Focus position")
            P.ylabel("FWHM (pixel)")
            P.savefig(filename)

    def log (self, filename):
        
        log = open(filename, "w")

        print >> log, time.strftime("%c")
        print >> log, "# A=%f B=%f C=%f" % tuple(self)
        print >> log, "# best focus position: %.3f (FWHM %.3f)" % self.best_focus

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
    def fit (position, fwhm):

        A, B, C = N.polyfit(position, fwhm, 2)

        fwhm_fit = N.polyval([A,B,C], position)
        
        err = sqrt(sum((fwhm_fit - fwhm)**2) / len(position))

        fit = FocusFit()
        fit.position = position
        fit.fwhm = fwhm

        fit.A, fit.B, fit.C = A,B,C
        fit.err = err
        fit.fwhm_fit = fwhm_fit

        return fit
    
class Autofocus (ChimeraObject):
    
    """
    Auto focuser
    ============

    This instrument have two modes of operation: in the first one, it will try
    to characterizes the current system and fit a parabola to a curve made of a
    star FWHM versus focus positions. Once we have this curve, focus the scope
    it's a interpolation problem with some offsets needed to compensate
    temperature.

    The second mode move the focuser In and OUT and use the fit information to
    fit a parabola using parameters found in FIT mode. The vertice of this new
    fitted parabola will give the best focus position.

    To the first mode, the algorithm its the following:

    1. determine target telescope position.
       if CURRENT, will use current telescope position.
       
       if OBJECT: will use target_ra, target_dec or target_name to
       move telescope to selected field.
       
       if AUTO: get site details and ask catalog manager to give us a
       list of stars available to focus now.
    
    2) take exposure to find focus star.

       If no star was found and in AUTO target mode, try another
       one. otherwise, abort the process.

    3) set window and binning if necessary and start iteration:

       Get n points starting at min_pos and ending at max_pos focus positions,
       and for each position measure FWHM of a target star (currently the
       brighter star in the field).

       Fit a parabola to the FWHM points measured.

    4) Leave focuser at best focus point (parabola vertice)

    The second mode use almost the same steps as the first one but using less
    points to fit the parabola.
    

    """

    __config__ = {"telescope"          : "/Telescope/fake",
                  "camera"             : "/Camera/fake",
                  "filterwheel"        : "/FilterWheel/fake",
                  "focuser"            : "/Focuser/fake",
                  "weather"            : "",
                  
                  "focus_on_subwindow" : True,
                  "focus_with_binning" : False,
                  "binning"            : Binning._2x2,
                  
                  "save_frames"        : False,
                  
                  "max_stars_to_try"   : 5,
                  
                  "step_size"          : 60,

                  "metric"             : Metric.FWHM,

                  "debug"              : False,
                  "debug_path"         :""
                  
                  }

    def __init__ (self):
        ChimeraObject.__init__ (self)

        self.exptime = None
        self.filter  = None

        self.best_fit = None

        self._debug_images = []
        self._debug_image = 0

    def getTel(self):
        return self.getManager().getProxy(self["telescope"])

    def getCam(self):
        return self.getManager().getProxy(self["camera"])

    def getFilter(self):
        return self.getManager().getProxy(self["filterwheel"])

    def getFocuser(self):
        return self.getManager().getProxy(self["focuser"])

    @lock
    def focus (self, mode=Mode.FOCUS, target=Target.AUTO, position=None,
               filter=None, exptime=None,
               start=2000, end=6000, points=20):

        # images for debug mode
        if self["debug"] and not self._debug_images:
            self._debug_images = [ "%s/image-%02d.fits" % (self["debug_path"], i)
                                   for i in range(points+1) ]
                
        self.exptime = exptime or 10
        self.filter = filter

        self.log.debug("Starting autofocus run.")

        # 1. Find star to focus

        if target == Target.AUTO:
            target_position = self._findStarToFocus()

        if target != Target.CURRENT:
            self.log.debug("Trying to move to focus star at %s." % position)

            tel = self.getTel()
            tel.slewToRaDec(target_position)
            
        else:
            self.log.debug("Will look for stars in the current telescope position")

        # 2. Find best star to focus on this field

        star_found = self._findBestStarToFocus(self._takeImageAndResolveStars())

        if not star_found:

            if not mode == Target.AUTO:
                raise StarNotFoundException("Could't find a suitable star to focus on.")

            tries = 1

            while not star_found and tries <= self["max_stars_to_try"]:
                star_found = self._findBestStarToFocus(self._takeImageAndResolveStars())
                tries += 1
                
            if not star_found:
                raise StarNotFoundException("Could't find a suitable star to focus on. "
                                            "Giving up after %d tries." % tries)

        if mode == Mode.FIT:

            try:
                fit = self._fitFocus(start, end, points)

                if not self.best_fit or fit < self.best_fit:
                    self.best_fit = fit
            except Exception, e:
                printException(e)

        else:
            if not self.best_fit:
                raise FocusNotFoundException("There is no fit information. Run FIT mode first.")


    def _fitFocus (self, start, end, points):
        
        focuser = self.getFocuser()
        initial_position = focuser.getPosition()

        self.log.debug("Initial focus position: %04d" % initial_position)

        positions = N.linspace(start, end, points, False)
        fwhm  = N.zeros(len(positions))

        for i, position in enumerate(positions):

            self.log.debug("Moving focuser to %d" % int(position))

            focuser.moveTo(position)

            star = self._findBrighterStar(self._takeImageAndResolveStars())

            self.log.debug("Adding star to curve. %s" % star)
            fwhm[i] = star["FWHM_IMAGE"]

        # fit a parabola to the points and save parameters
        try:
            fit = FocusFit.fit(positions, fwhm)
        except Exception, e:
            focuser.moveTo(initial_position)

            raise FocusNotFoundException("Error trying to fit a focus curve. "
                                         "Leaving focuser at %04d" % initial_position)
            


        # save a plot
        if self["debug"]:
            fit.plot("focus.png")
            fit.log("focus.log")

        # leave focuser at best position
        self.log.debug("Best focus position: %.3f" % fit.best_focus[0])
        focuser.moveTo(fit.best_focus[0])

        return fit
    
    def _takeImageAndResolveStars (self):

        frame = self._takeImage()
        stars = self._findStars(frame)

        return stars

    def _takeImage (self):

        if self["debug"]:
            frame = self._debug_images[self._debug_image]
            self._debug_image += 1
            return frame

        if not self["save_frames"]:
            filename = tempfile.mkstemp(suffix=".fits")[0]
        else:
            filename = "focus-sequence"

        cam = self.getCam()
        
        frame = cam.expose(exp_time=self.exptime,
                           frames=1, shutter=Shutter.OPEN,
                           filename=filename)

        return frame[0]

    def _findStars (self, fits_file):

        sex = SExtractor ()

        sex.config['PIXEL_SCALE'] = 0.45
        sex.config['BACK_TYPE']   = "AUTO"

        sex.config['SATUR_LEVEL'] = 60000

        # improve speed with higher threshold
        sex.config['DETECT_THRESH'] = 3.0

        # no output, please
        sex.config['VERBOSE_TYPE'] = "QUIET"

        # our "star" dict entry will contain all this members
        sex.config['PARAMETERS_LIST'] = ["NUMBER",
                                         "XWIN_IMAGE", "YWIN_IMAGE",
                                         "FLUX_BEST", "FWHM_IMAGE",
                                         "FLAGS"]

        # ok, here we go!
        sex.run(fits_file)

        result = sex.catalog()

        sex.clean(config=True, catalog=True, check=True)

        return result

    def _findBestStarToFocus (self, catalog):

        # simple plan: brighter star
        return self._findBrighterStar(catalog)

    def _findBrighterStar (self, catalog):

        fluxes = [star for star in catalog if star["FLAGS"] == 0]

        if not fluxes: # empty catalog
            return False

        return max(fluxes, key=lambda star: star["FLUX_BEST"])
        
