#import chimera.core.log

from chimera.core.remoteobject import RemoteObject
from chimera.core.exceptions import ChimeraException
from chimera.core.version import _chimera_name_, _chimera_long_description_

from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.sextractor import SExtractor

from astropy.io import fits
from astropy import wcs

import numpy as N

import os
import string
import datetime as dt

import bz2
import gzip
import zipfile

import sys
import shutil

from UserDict import DictMixin

import logging
log = logging.getLogger(__name__)


class WCSNotFoundException (ChimeraException):
    pass


class ImageUtil (object):

    @staticmethod
    def formatDate(datetime):
        if type(datetime) == float:
            datetime = dt.datetime.fromtimestamp(datetime)

        return datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @staticmethod
    def makeFilename(path='$DATE-$TIME',
                     subs={},
                     dateFormat="%Y%m%d",
                     timeFormat="%H%M%S"):
        """
        Helper method to create filenames with increasing sequence number
        appended.
        It can do variable substitution in the given path. Standard
        variables are $DATE and $TIME (you can define the format of
        these field passint the appropriate format string in
        dateFormat and timeFormat, respectively).
        Any other variable can be defined passing an subs dictionary
        with key as variable name.

        @param path: Filename path, with directories, environmnt variables.
        @type  path: str

        @param subs: Dictionary of {VAR=NAME,...} to create aditional
                     variable substitutions.
        @type subs: dict

        @param dateFormat: Date format, as used in time.strftime, to
                           be used by $DATE variable.
        @type dateFormat: str

        @param timeFormat: Time format, as used in time.strftime, to
                           be used by $TIME variable.
        @type timeFormat: str

        @return: Filename.
        @rtype: str
        """

        localtime = dt.datetime.now()
        utctime = dt.datetime.utcnow()

        if localtime.hour < 12:
            jd_day = localtime - dt.timedelta(days=1)
        else:
            jd_day = localtime

        subs_dict = {"LAST_NOON_DATE": jd_day.strftime(dateFormat),
                     "DATE": utctime.strftime(dateFormat),
                     "TIME": utctime.strftime(timeFormat)}

        # add any user-specific keywords
        subs_dict.update(subs)

        dirname, filename = os.path.split(path)
        dirname = os.path.expanduser(dirname)
        dirname = os.path.expandvars(dirname)
        dirname = os.path.realpath(dirname)

        basename, ext = os.path.splitext(filename)
        if not ext:
            ext = "fits"
        else:
            # remove first dot
            ext = ext[1:]

        # make substitutions
        dirname = string.Template(dirname).safe_substitute(subs_dict)
        basename = string.Template(basename).safe_substitute(subs_dict)
        ext = string.Template(ext).safe_substitute(subs_dict)

        fullpath = os.path.join(dirname, basename)
        finalname = os.path.join(dirname, "%s%s%s" % (basename, os.path.extsep, ext))

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if not os.path.isdir(dirname):
            raise OSError(
                "A file with the same name as the desired directory already exists. ('%s')" % dirname)

        # If filename exists, append -NNN to the end of the file name.
        # A maximum of 1000 files can be generated with the same filename.
        if os.path.exists(finalname):
            base, ext = os.path.splitext(finalname)
            i = 1
            while os.path.exists("%s-%03i%s" % (base, i, ext)):
                i += 1
                if i == 1000:
                    raise OSError("Reached the maximum of 999 files with the same name (%s)." % finalname)

            finalname = "%s-%03i%s" % (base, i, ext)

        return finalname


class Image (DictMixin, RemoteObject):

    """
    Class to manipulate FITS images with a Pythonic taste.

    The underlying framework comes from astropy.io.fits library
    and astropy.wcs to get WCS info (which as matter of fact use
    WCSlib from Mark Calabretta). In addition, we use a wrapper to
    E. Bertin SExctractor's written by Laurent Le Guillou. Thank you all guys.

    Besides image functions, this class acts like a dictionary of FITS
    headers. Use it just like any Python dict.

    This class currently support only single extension IMAGE FITS
    files.
    """

    @staticmethod
    def fromFile(filename, fix = False, mode = "update"):
        fd = fits.open(filename, mode = mode)
        img = Image(filename, fd)

        if fix:
            img.fix()

        return img

    @staticmethod
    def create(data, imageRequest=None, filename=None):

        if imageRequest:
            try:
                filename = imageRequest["filename"]
            except KeyError:
                if not filename:
                    raise TypeError("Invalid filename, you must pass filename=something"
                                    "or a valid ImageRequest object")

        filename = ImageUtil.makeFilename(filename)

        hdu = fits.PrimaryHDU(data)

        headers = [("DATE", ImageUtil.formatDate(dt.datetime.utcnow()), "date of file creation"),
                   ("AUTHOR", _chimera_name_, 'author of the data'),
                   ("FILENAME", os.path.basename(filename), "name of the file")]

        # TODO: Implement BITPIX support
        hdu.scale('int16', '', bzero=32768, bscale=1)

        if imageRequest:
            headers += imageRequest.headers

        for header in headers:
            try:
                hdu.header.set(*header)
            except Exception, e:
                log.warning("Couldn't add %s: %s" % (str(header), str(e)))

        hduList = fits.HDUList([hdu])
        hduList.writeto(filename)
        hduList.close()

        del hduList
        del hdu

        return Image.fromFile(filename)

    #
    # standard constructor
    #
    def __init__(self, filename, fd):
        RemoteObject.__init__(self)

        self._fd = fd
        self._filename = filename
        self._http = None
        self._wcs = None

    filename = lambda self: self._filename

    def close(self):
        self._fd.close()


    def http(self, http=None):
        if http:
            self._http = http
        return self._http

    def __str__(self):
        return "<Image %s>" % self.filename()

    #
    # serialization support
    # we close before pickle and reopen after it
    #
    def __getstate__(self):
        self._fd.close()
        return self.__dict__

    def __setstate__(self, args):
        self.__dict__ = args
        self._fd = fits.open(self._filename, mode="update")

    #
    # geometry
    #

    width = lambda self: self["NAXIS1"]
    height = lambda self: self["NAXIS2"]

    size = lambda self: (self.width(), self.height())

    center = lambda self: (self.width() / 2.0, self.height() / 2.0)

    #
    # WCS
    #

    def pixelAt(self, *world):

        if not self._findWCS():
            return (0, 0)

        pixel = self._valueAt(self._wcs.wcs_world2pix, *world)

        # round pixel to avoid large decimal numbers and get out strange -0
        pixel = list(round(p, 6) for p in pixel)

        if pixel[0] == (-0.0):
            pixel[0] = 0.0
        if pixel[1] == (-0.0):
            pixel[1] = 0.0

        return tuple(pixel)

    def worldAt(self, *pixel):

        if not self._findWCS():
            return Position.fromRaDec(0, 0)

        world = self._valueAt(self._wcs.wcs_pix2world, *pixel)
        return Position.fromRaDec(Coord.fromD(world[0]), Coord.fromD(world[1]))

    def _findWCS(self):

        if not self._wcs:
            try:
                self._wcs = wcs.WCS(self._fd["PRIMARY"].header)
            except (KeyError, ValueError), e:
                raise WCSNotFoundException(
                    "Couldn't find WCS information on %s ('%s')" % (self._filename, e))

        return True

    def _valueAt(self, fn, *coords):
        """
        Accepts a function callback and variable coords.

        If len(coords) == 1 convert (from tuple or Position) to decimal degress.
        If len(coords) == 2, convert (from number or Coord) to decimal degress
        """

        assert len(coords) >= 1
        assert self._wcs is not None

        if len(coords) == 2:
            c1 = Coord.fromH(coords[0]).D
            c2 = Coord.fromD(coords[1]).D
        else:
            if isinstance(coords[0], Position):
                c1, c2 = coords[0].dd()
            else:  # assumes as tuple
                c1, c2 = coords[0]

        value = fn(N.array([[c1, c2]]), 1)

        if len(value) >= 1:
            return tuple(value[0])
        else:
            raise WCSNotFoundException("Couldn't convert coordinates.")

    #
    # Source extraction
    #

    def extract(self, params={}, saveCatalog=False, saveConfig=False):

        sex = SExtractor()

        # default params
        sex.config['PIXEL_SCALE'] = 0.45
        sex.config['BACK_TYPE'] = "AUTO"
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
        try:
            sex.run(self._filename, clean=False)
            result = sex.catalog()
            return result
        finally:
            if saveCatalog:
                shutil.move(sex.config['CATALOG_NAME'], saveCatalog)
            if saveConfig:
                shutil.move(sex.config['CONFIG_FILE'], saveConfig)

            sex.clean(config=True, catalog=True, check=True)

    #
    # I/O and verification
    #

    def fix(self):
        self._fd.verify('fix')

    def save(self, filename=None, verify='exception'):

        if filename:
            self._fd.writeto(filename, output_verify=verify)
        else:
            self._fd.flush(output_verify=verify)

        return True

    def _doCompress(self, filename, format):
        if format.lower() == "bz2":
            bzfilename = filename + '.bz2'
            bzfp = bz2.BZ2File(bzfilename, 'wb', compresslevel=4)
            rawfp = open(filename)
            bzfp.write(rawfp.read())
            bzfp.close()
            rawfp.close()
            os.unlink(filename)
        elif format.lower() == "gzip":
            gzfilename = filename + '.gz'
            gzfp = gzip.GzipFile(gzfilename, 'wb', compresslevel=5)
            rawfp = open(filename)
            gzfp.write(rawfp.read())
            gzfp.close()
            rawfp.close()
            os.unlink(filename)
        else:  # zip
            zipfilename = filename + '.zip'
            zipfp = zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED)
            zipfp.write(filename, os.path.basename(filename))
            zipfp.close()
            os.unlink(filename)

    def compress(self, format="bz2", multiprocess=False):

        if multiprocess and sys.version_info[0:2] >= (2, 6):
            from multiprocessing import Process
            p = Process(
                target=self._doCompress, args=(self.filename(), format))
            p.start()
        else:
            self._doCompress(self.filename(), format)

    # dict mixin implementation for headers
    def __getitem__(self, key):
        return self._fd["PRIMARY"].header.__getitem__(key)

    def __setitem__(self, key, value):

        if not key in self:
            self += (key, value)
            return True

        return self._fd["PRIMARY"].header.__setitem__(key, value)

    def __delitem__(self, key):
        return self._fd["PRIMARY"].header.__delitem__(key)

    def keys(self):
        return [item[0] for item in self._fd["PRIMARY"].header.items()]

    def items(self):
        return self._fd["PRIMARY"].header.items()

    def __contains__(self, key):
        return key in self._fd["PRIMARY"].header

    def __iter__(self):
        for k in self.keys():
            yield k

    def iteritems(self):
        for item in self.items():
            yield item

    def __iadd__(self, headers):
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
            self._fd["PRIMARY"].header.set(*header)

        self.save()

        return self
