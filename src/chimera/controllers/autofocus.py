
import logging
import tempfile

from chimera.core.lifecycle import BasicLifeCycle
from chimera.util.sextractor import SExtractor

class Autofocus (BasicLifeCycle):
    
    """
    Auto focus algorithm:
    
    1) determine target
       if current:  go to 2.
       if object: use target_ra, target_dec to move telescope
       if auto: get site details and ask catalog manager to give us a list of stars available to focus.
    
    2) take exposure to find focus star
       if not found and auto: try another one
       else: go to 3
    
    3) set window and binning if necessary and start iteration:
       if direction_hint: move to that direction, else guess from calibration.
       iterate (until max_terations), measure the selected metric until find a minimun       
         
    """

    __config__ = {"telescope"          : "/Telescope/fake",
                  "camera"             : "/Camera/fake",
                  "filterwheel"        : "/FilterWheel/fake",
                  "focuser"            : "/Focuser/fake",
                  "target"             : ["auto", "current", "object"],
                  "target_ra"          : "",
                  "target_dec"         : "",
                  "filter"             : "",
                  "exp_time"           : -1,
                  "focus_on_subwindow" : True,
                  "focus_with_binning" : False,
                  "binning"            : "",
                  "save_frames"        : False,
                  "save_frames_dir"    : "",
                  "max_iterations"     : 10,
                  "max_stars_to_try"   : 5,
                  "direction_hint"     : ["auto", "in", "out"],
                  "step_size"          : 10,
                  "metric"             : ["fwhm", "hfd"]
                  }

    def __init__ (self, manager):
        BasicLifeCycle.__init__ (self, manager)

        self.tel     = None
        self.filter  = None
        self.cam     = None
        self.focuser = None

    def init (self, config):

        self.config += config

        self.tel     = self.manager.getInstrument (self.config.telescope)
        self.filter  = self.manager.getInstrument (self.config.filter)
        self.cam     = self.manager.getInstrument (self.config.camera)
        self.focuser = self.manager.getInstrument (self.config.focuser)

        if None in [self.tel, self.filter, self.cam, self.focuser]:
            logging.warning ("something wrong with your setup.")
            return False

        return True
        
    def autoFocus (self):

        #
        # 1
        #

        # FIXME: TBD
        

        #
        # 2
        #

        star_to_focus = self._findBestStarToFocus (self._takeImageAndResolveStars())

        if not star_to_focus:
            logging.warning ("Can't found a suitable star to focus on.")
            return False
        
        #
        # 3
        #

        # FIXME: use hint
        #  1 => in
        # -1 => out

        direction = 1
        direction_changed = False
        
        focus_stack = []
        focus_stack.append (self.focuser.getPosition())

        last_fwhm = star_to_focus["FWHM_IMAGE"]

        for step in range (self.max_iterations):

            if not self._moveFocus (direction):
                logging.warning ("Can't move focuser. Giving up.")
                return False

            star = self._findBrighterStar (self._takeImageAndResolveStars())

            if star["FWHM_IMAGE"] < last_fwhm:
                focus_stack.append (self.focuser.getPosition())
                last_fwhm = star["FWHM_IMAGE"]
                continue

            if star["FWHM_IMAGE"] > last_fwhm:

                # if worse again, give up on last good position
                if direction_changed:
                    self.focuser.moveTo (focus_stack.pop())
                    return True
                
                direction *= -1
                direction_changed = True
                continue

        # if we reach here, we are in problems...
        # after max_iterations we cannot got a good focus
        return False

    def _takeImageAndResolveStars (self):

        frame = self._takeImage (self.config.exp_time)

        if not frame:
            logging.warning ("Couldn't take exposure."
                             "Autofocus can't continue.")
            return False

        stars = self._findStars (frame)

        return stars

    def _takeImage (self, exp_time = None):

        config = {"exp_time"	 : exp_time or self.config.exp_time,
                  "shutter" 	 : "open",
                  "date_format"	 : "%d%m%y-%H%M%S",                  
                  "file_format"	 : "focus-$date-%s" % tempfile.mktemp(),
                  "directory"	 : tempfile.gettempdir(),
                  "observer"	 : "Focus Observer",
                  "obj_name"	 : "focus"}

        ret = self.cam.expose (config)

        return ret

    def _findStars (self, fits_file):

        sex = SExtractor ()

        # use wcs info to determine pixel scale
        sex.config['PIXEL_SCALE'] = 0
        
        #sex.config['SATUR_LEVEL'] = 40000

        # improve speed with higher threshold
        sex.config['DETECT_THRESH'] = 3.0

        # automatic background determination and subtraction
        sex.config['BACK_TYPE'] = "AUTO"

        # no output, please
        sex.config['VERBOSE_TYPE'] = "QUIET"

        # our "star" dict entry will contain all this members
        sex.config['PARAMETERS_LIST'] = ["NUMBER", "X_IMAGE", "Y_IMAGE", "FLUX_BEST", "FWHM_IMAGE", "FLAGS"]

        # ok, here we go!
        sex.run(fits_file)

        result = sex.catalog()

        sex.clean(config=True, catalog=True, check=True)

        return result

    def _moveFocus (self, direction):

        ret = None

        if direction > 0:
            ret = self.focuser.moveIn (self.config.step_size)
        else:
            ret = self.focuser.moveOut (self.config.step_size)

        return ret

    def _findBestStarToFocus (self, catalog):

        # FIXME: better heuristic
        # simple plan: brighter star
        return self._findBrigherStar ()

    def _findBrighterStar (self, catalog):

        if not catalog:
            return False

        max_flux = max ([star["FLUX_BEST"] for star in catalog if star["FLAGS"] == 0])

        # search the required star (simple O(n) search)
        for star in catalog:
            if star["FLUX_BEST"] == max_flux:
                return star

        return False
