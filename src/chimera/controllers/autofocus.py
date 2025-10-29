import logging
import ntpath
import os
import time
from math import sqrt

import numpy as np
import yaml

from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.controllers.imageserver.util import get_image_server
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY
from chimera.core.exceptions import ChimeraException, ClassLoaderException
from chimera.core.lock import lock
from chimera.interfaces.autofocus import Autofocus as IAutofocus
from chimera.interfaces.autofocus import FocusNotFoundException, StarNotFoundException
from chimera.interfaces.focuser import InvalidFocusPositionException
from chimera.util.image import Image, ImageUtil
from chimera.util.output import green, red

try:
    import matplotlib.pyplot as plt

    plot = True
except (ImportError, RuntimeError, ClassLoaderException):
    plot = False


class FocusFit:

    def __init__(self):

        # input
        self.temperature = None
        self.position = None
        self.fwhm = None
        self.minmax = None

        # calculated
        self.a = 0
        self.b = 0
        self.c = 0

        self.fwhm_fit = None
        self.err = 1e20

    best_focus = property(
        lambda self: (
            -self.B / (2 * self.A),
            (-self.B**2 + 4 * self.A * self.C) / (4 * self.A),
        )
    )

    def plot(self, filename):

        global plot

        if plot:
            plt.figure(1)
            plt.plot(self.position, self.fwhm, "ro", label="data")
            plt.plot(self.position, self.fwhm_fit, "b--", label="fit")
            plt.plot(
                [self.best_focus[0]],
                [self.best_focus[1]],
                "bD",
                label="best focus from fit",
            )

            if self.minmax:
                plt.ylim(*self.minmax)

            plt.title("Focus")
            plt.xlabel("Focus position")
            plt.ylabel("FWHM (pixel)")
            plt.savefig(filename)

    def log(self, filename):

        log = open(filename, "w")

        print("#", time.strftime("%c"), file=log)
        print("# A={:f} B={:f} C={:f}".format(*tuple(self)), file=log)
        print(
            "# best focus position: {:.3f}(FWHM {:.3f})".format(*self.best_focus),
            file=log,
        )
        if self.minmax:
            print(f"# minmax filtering: {str(self.minmax)}", file=log)

        if self.temperature:
            print(f"# focuser temperature: {self.temperature:.3f}", file=log)

        for position, fwhm in zip(self.position, self.fwhm):
            print(position, fwhm, file=log)

        log.close()

    def __iter__(self):
        return (self.a, self.b, self.c).__iter__()

    def __cmp__(self, other):
        if isinstance(other, FocusFit):
            return self.err - other.err
        else:
            return self.err - other

    def __hash__(self):
        return hash((self.a, self.b, self.c, self.err))

    def __bool__(self):
        return (self.position is not None) and (self.fwhm is not None)

    @staticmethod
    def fit(position, fwhm, temperature=None, minmax=None):

        if minmax and len(minmax) >= 2:
            idxs = (fwhm >= minmax[0]) & (fwhm <= minmax[1])
            position = position[idxs]
            fwhm = fwhm[idxs]

        a, b, c = np.polyfit(position, fwhm, 2)

        fwhm_fit = np.polyval([a, b, c], position)

        err = sqrt(sum((fwhm_fit - fwhm) ** 2) / len(position))

        fit = FocusFit()
        fit.position = position
        fit.fwhm = fwhm
        fit.temperature = temperature
        fit.minmax = minmax

        fit.a, fit.b, fit.c = a, b, c
        fit.err = err
        fit.fwhm_fit = fwhm_fit

        return fit


class Autofocus(ChimeraObject, IAutofocus):
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

    def __init__(self):
        ChimeraObject.__init__(self)

        self.image_request = None
        self.filter = None

        self.current_run = None

        self.best_fit = None

        self._debugging = False
        self._debug_images = []
        self._debug_image = 0

        self._log_handler = None

    def get_cam(self):
        return self.get_proxy(self["camera"])

    def get_filter(self):
        return self.get_proxy(self["filterwheel"])

    def get_focuser(self):
        return self.get_proxy(self["focuser"])

    def _get_id(self):
        return "autofocus-{}".format(time.strftime("%Y%m%d-%H%M%S"))

    def _open_logger(self):

        if self._log_handler:
            self._close_logger()

        self._log_handler = logging.FileHandler(
            os.path.join(SYSTEM_CONFIG_DIRECTORY, self.current_run, "autofocus.log")
        )
        self._log_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
        self._log_handler.setLevel(logging.DEBUG)
        self.log.addHandler(self._log_handler)

    def _close_logger(self):
        if self._log_handler:
            self.log.removeHandler(self._log_handler)
            self._log_handler.close()

    @lock
    def focus(
        self,
        filter=None,
        exptime=None,
        binning=None,
        window=None,
        start=2000,
        end=6000,
        step=500,
        minmax=(0, 30),
        debug=False,
    ):

        self._debugging = debug

        self.current_run = self._get_id()

        if not os.path.exists(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.current_run)):
            os.mkdir(os.path.join(SYSTEM_CONFIG_DIRECTORY, self.current_run))

        self._open_logger()

        if debug:
            debug_file = open(os.path.join(debug, "autofocus.debug"))
            debug_data = yaml.load(debug_file.read())

            start = debug_data["start"]
            end = debug_data["end"]
            step = debug_data["step"]

            debug_file.close()

        positions = np.arange(start, end + 1, step)

        if not debug:
            # save parameter to ease a debug run later
            debug_data = dict(id=self.current_run, start=start, end=end, step=step)
            try:
                debug_file = open(
                    os.path.join(
                        SYSTEM_CONFIG_DIRECTORY, self.current_run, "autofocus.debug"
                    ),
                    "w",
                )
                debug_file.write(yaml.dump(debug_data))
                debug_file.close()
            except OSError:
                self.log.warning(
                    "Cannot save debug information. Debug will be a little harder later."
                )

        self.log.debug("=" * 40)
        self.log.debug("[{}] Starting autofocus run.".format(time.strftime("%c")))
        self.log.debug("=" * 40)
        self.log.debug(
            f"Focus range: start={start} end={end} step={step} points={len(positions)}"
        )

        # images for debug mode
        if debug:
            self._debug_images = [
                f"{debug}/focus-{i:04d}.fits" for i in range(1, len(positions) + 2)
            ]

        self.image_request = ImageRequest()
        self.image_request["exptime"] = exptime or 10
        self.image_request["frames"] = 1
        self.image_request["shutter"] = "OPEN"

        if filter:
            self.filter = filter
            self.log.debug(f"Using filter {self.filter}.")
        else:
            self.filter = False
            self.log.debug("Using current filter.")

        if binning:
            self.image_request["binning"] = binning

        if window:
            self.image_request["window"] = window

        # 1. Find best star to focus on this field

        star_found = self._find_best_star_to_focus(self._take_image_and_resolve_stars())

        if not star_found:

            tries = 0

            while not star_found and tries < self["max_tries"]:
                star_found = self._find_best_star_to_focus(
                    self._take_image_and_resolve_stars()
                )
                tries += 1

            if not star_found:
                raise StarNotFoundException(
                    f"Couldn't find a suitable star to focus on. Giving up after {tries} tries."
                )

        try:
            fit = self._fit_focus(positions, minmax)

            if not self.best_fit or fit < self.best_fit:
                self.best_fit = fit

            return {
                "current_run": self.current_run,
                "A": fit.a,
                "B": fit.b,
                "C": fit.c,
                "best": int(fit.best_focus[0]),
            }

        finally:
            # reset debug counter
            self._debug_image = 0

    def _fit_focus(self, positions, minmax=None):

        focuser = self.get_focuser()
        initial_position = focuser.get_position()

        self.log.debug(f"Initial focus position: {initial_position:04d}")

        fwhm = []
        valid_positions = []

        for i, position in enumerate(positions):

            self.log.debug(f"Moving focuser to {int(position)}")

            focuser.move_to(position)

            frame_path, frame = self._take_image()
            stars = self._find_stars(frame_path)
            star = self._find_brighter_star(stars)

            star["CHIMERA_FLAGS"] = green("OK")

            if abs(star["FWHM_IMAGE"] - 4.18) <= 0.02:
                self.log.debug(
                    f"Ignoring star at (X,Y)=({star['XWIN_IMAGE']},{star['YWIN_IMAGE']}) FWHM magic number={star['FWHM_IMAGE']:.3f}, FLUX={star['FLUX_BEST']:.3f}"
                )
                star["CHIMERA_FLAGS"] = red("Ignoring, SExtractor FWHM magic number.")
            elif star["FWHM_IMAGE"] <= minmax[0] or star["FWHM_IMAGE"] >= minmax[1]:
                self.log.debug(
                    f"Ignoring star at (X,Y)=({star['XWIN_IMAGE']},{star['YWIN_IMAGE']}) FWHM magic number={star['FWHM_IMAGE']:.3f}, FLUX={star['FLUX_BEST']:.3f}"
                )
                star["CHIMERA_FLAGS"] = red("Ignoring, FWHM above/below minmax limits.")
            else:
                self.log.debug(
                    f"Adding star to curve. (X,Y)=({star['XWIN_IMAGE']},{star['YWIN_IMAGE']}) FWHM={star['FWHM_IMAGE']:.3f} FLUX={star['FLUX_BEST']:.3f}"
                )
                fwhm.append(star["FWHM_IMAGE"])
                valid_positions.append(position)

            self.step_complete(position, star, frame_path)

        # fit a parabola to the points and save parameters
        try:
            if minmax:
                self.log.debug("Minmax filtering FWHM ({:.3f},{:.3f})".format(*minmax))

            try:
                temp = focuser.get_temperature()
            except NotImplementedError:
                temp = None
            fit = FocusFit.fit(
                np.array(valid_positions),
                np.array(fwhm),
                temperature=temp,
                minmax=minmax,
            )
        except Exception:
            focuser.move_to(initial_position)

            raise FocusNotFoundException(
                f"Error trying to fit a focus curve. Leaving focuser at {initial_position:04d}"
            )

        fit.plot(
            os.path.join(
                SYSTEM_CONFIG_DIRECTORY, self.current_run, "autofocus.plot.png"
            )
        )
        fit.log(
            os.path.join(
                SYSTEM_CONFIG_DIRECTORY, self.current_run, "autofocus.plot.dat"
            )
        )

        # leave focuser at best position
        try:
            if np.isnan(fit.best_focus[0]):
                raise FocusNotFoundException(
                    "Focus fitting error: fitting do not converges (NaN result). See logs for more info."
                )

            self.log.debug(f"Best focus position: {fit.best_focus[0]:.3f}")
            focuser.move_to(int(fit.best_focus[0]))
        except InvalidFocusPositionException as e:
            focuser.move_to(initial_position)
            raise FocusNotFoundException(
                f"Best guess was {str(fit.best_focus[0])}, but could not move the focuser.\n"
                f"{str(e)}\n"
                "Returning to initial position."
            )

        return fit

    def _take_image_and_resolve_stars(self):

        frame_path, frame = self._take_image()
        stars = self._find_stars(frame_path)

        return stars

    def _take_image(self):

        if self._debugging:
            try:
                frame = self._debug_images[self._debug_image]
                self._debug_image += 1

                img = Image.from_file(frame)
                srv = get_image_server(self.get_manager())
                return srv.register(img)
            except IndexError:
                raise ChimeraException("Cannot find debug images")

        self.image_request["filename"] = os.path.basename(
            ImageUtil.make_filename("focus-$DATE")
        )

        cam = self.get_cam()

        if self.filter:
            filter = self.get_filter()
            filter.set_filter(self.filter)

        frames = cam.expose(self.image_request)

        if frames:
            image = frames[0]
            image_path = image.filename
            if not os.path.exists(
                image_path
            ):  # If image is on a remote server, donwload it.

                #  If remote is windows, image_path will be c:\...\image.fits, so use ntpath instead of os.path.
                if ":\\" in image_path:
                    modpath = ntpath
                else:
                    modpath = os.path
                image_path = ImageUtil.make_filename(
                    os.path.join(
                        get_image_server(self.get_manager()).default_night_dir(),
                        modpath.basename(image_path),
                    )
                )
                t0 = time.time()
                self.log.debug(f"Downloading image from server to {image_path}")
                if not ImageUtil.download(image, image_path):
                    raise ChimeraException(
                        f"Error downloading image {image_path} from {image.http()}"
                    )
                self.log.debug(
                    "Finished download. Took %3.2f seconds" % (time.time() - t0)
                )
            return image_path, image
        else:
            raise Exception("Could not take an image")

    def _find_stars(self, frame_path):

        frame = Image.from_file(frame_path)

        config = {}
        config["PIXEL_SCALE"] = 0  # use WCS info
        config["BACK_TYPE"] = "AUTO"

        # CCD saturation level in ADUs.
        s = self.get_cam()["ccd_saturation_level"]
        if (
            s is not None
        ):  # If there is no ccd_saturation_level on the config, use the default.
            config["SATUR_LEVEL"] = s

        # improve speed with higher threshold
        config["DETECT_THRESH"] = 3.0

        # no output, please
        config["VERBOSE_TYPE"] = "QUIET"

        # our "star" dict entry will contain all this members
        config["PARAMETERS_LIST"] = [
            "NUMBER",
            "XWIN_IMAGE",
            "YWIN_IMAGE",
            "FLUX_BEST",
            "FWHM_IMAGE",
            "FLAGS",
        ]

        aux_fname = os.path.join(
            SYSTEM_CONFIG_DIRECTORY,
            self.current_run,
            os.path.splitext(os.path.basename(frame_path))[0],
        )
        catalog_name = aux_fname + ".catalog"
        config_name = aux_fname + ".config"
        return frame.extract(config, saveCatalog=catalog_name, saveConfig=config_name)

    def _find_best_star_to_focus(self, catalog):

        # simple plan: brighter star
        # FIXME: avoid "border" stars
        return self._find_brighter_star(catalog)

    def _find_brighter_star(self, catalog):

        fluxes = [star for star in catalog if star["FLAGS"] == 0]

        if not fluxes:  # empty catalog
            return False

        return max(fluxes, key=lambda star: star["FLUX_BEST"])


if __name__ == "__main__":

    x = Autofocus()
    # x.check_pointing()
    x._take_image()
