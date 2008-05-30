
from chimera.core.exceptions import ChimeraException

from chimera.util.coord import Coord
from chimera.util.position import Position

from chimera.util.sextractor import SExtractor

import pyfits
import numpy as N
import pywcs

import sys
from UserDict import DictMixin


class WCSNotFoundException (ChimeraException):
    pass


class Image (DictMixin):
    """
    Class to manipulate FITS images with a Pythonic taste.

    The underlying framework comes from the very good PyFITS library
    with some PyWCS stuff to get WCS info (which as matter of fact use
    WCSlib from Mark Calabretta). In addition, we use a wrapper to
    E. Bertin SExctractor's written by Laurent Le Guillou. Thank you all guys.

    Besides image functions, this class acts like a dictionary of FITS
    headers. Use it just like any Python dict.

    This class currently support only single extension IMAGE FITS
    files.

    """

    @staticmethod
    def fromFile(filename, readonly=False, fix=True):

        if readonly:
            mode = 'readonly'
        else:
            mode = 'update'

        fd = pyfits.open(filename, mode)

        img = Image()
        img.filename = filename
        img.fd = fd
        img.readonly = readonly

        if fix:
            img.fix()

        return img

    def __init__ (self):
        self.filename = ""
        self.fd       = None
        self.readonly = False

        self._wcs = None

    #
    # geometry
    #
    
    width  = property(lambda self: self["NAXIS1"])
    height = property(lambda self: self["NAXIS2"])

    size = property(lambda self: (self.width, self.height))

    center = property(lambda self: (self.width/2.0, self.height/2.0))

    #
    # WCS
    #
    
    def pixelAt (self, *world):
        self._findWCS()
        pixel = self._valueAt(self._wcs.world2pixel_fits, *world)

        # round pixel to avoid large decimal numbers and get out strange -0
        pixel = list(round(p, 6) for p in pixel)

        if pixel[0] == (-0.0):
            pixel[0] = 0.0
        if pixel[1] == (-0.0):
            pixel[1] = 0.0
            
        return tuple(pixel)

    def worldAt (self, *pixel):
        self._findWCS()
        world = self._valueAt(self._wcs.pixel2world_fits, *pixel)
        return Position.fromRaDec(Coord.fromD(world[0]), Coord.fromD(world[1]))

    def _findWCS (self):

        if not self._wcs:
            try:
                self._wcs = pywcs.WCS(self.fd["PRIMARY"].header)
            except KeyError:
                raise WCSNotFoundException("Couldn't found WCS information on %s" % (self.filename))

    def _valueAt(self, fn, *coords):
        """
        Accepts a function callback and variable coords.

        If len(coords) == 1 convert (from tuple or Position) to decimal degress.
        If len(coords) == 2, convert (from number or Coord) to decimal degress
        """
        
        assert len(coords) >= 1
        assert self._wcs != None

        if len(coords) == 2:
            c1 = Coord.fromH(coords[0]).D
            c2 = Coord.fromD(coords[1]).D
        else:
            if isinstance(coords[0], Position):
                c1, c2 = coords[0].dd()
            else: # assumes as tuple
                c1, c2 = coords[0]

        value = fn([N.array([c1,c2])])

        if len(value) >= 1:
            return tuple(value[0])
        else:
            raise WCSNotFoundException("Couldn't convert coordinates.")

    #
    # Source extraction
    #
    
    def extract (self, params={}):

        sex = SExtractor ()

        # default params
        sex.config['PIXEL_SCALE'] = 0.45
        sex.config['BACK_TYPE']   = "AUTO"
        sex.config['SATUR_LEVEL'] = 60000
        sex.config['DETECT_THRESH'] = 3.0
        sex.config['VERBOSE_TYPE'] = "QUIET"
        sex.config['PARAMETERS_LIST'] = ["NUMBER",
                                         "XWIN_IMAGE", "YWIN_IMAGE",
                                         "FLUX_BEST", "FWHM_IMAGE",
                                         "FLAGS"]

        # update values from user params
        sex.config.update(params)

        # ok, here we go!
        sex.run(self.filename)

        result = sex.catalog()

        sex.clean(config=True, catalog=True, check=True)

        return result

    #
    # I/O and verification
    #
    
    def fix (self):
        self.fd.verify('fix')

    def save (self, filename=None, verify='exception'):
        if self.readonly and not filename:
            raise IOError("Cannot write. Image is readonly and no filename provided")
        
        if filename:
            self.fd.writeto(filename, output_verify=verify)
        else:
            self.fd.flush(output_verify=verify)

        return True

    # dict mixin implementation for headers
    def __getitem__ (self, key):
        return self.fd["PRIMARY"].header.__getitem__(key)
        
    def __setitem__ (self, key, value):
        return self.fd["PRIMARY"].header.__setitem__(key, value)

    def __delitem__ (self, key):
        return self.fd["PRIMARY"].header.__delitem__(key)

    def keys (self):
        return [item[0] for item in self.fd["PRIMARY"].header.items()]

    def items (self):
        return self.fd["PRIMARY"].header.items()
    
    def __contains__(self, key):
        return self.fd["PRIMARY"].header.has_key(key)

    def __iter__ (self):
        for k in self.keys():
            yield k

    def iteritems (self):
        for item in self.items():
            yield item

    def __iadd__ (self, headers):
        """
        Create new header keyworks using arithmetic operator +=.

        This method accepts tuples of values or lists of tuples of values.

        Each tuple must have 2 or more arguments. Each values is interpreted as:
           (key, value, comment=None, before=None, after=None)

        Where after and before marks the point of insertion of your
        new header.
        """

        if not isinstance(headers, list):
            headers = [headers]

        for header in headers:
            self.fd["PRIMARY"].header.update(*header)

        return self
