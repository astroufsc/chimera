import bz2
import datetime as dt
import gzip
import logging
import os
import shutil
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections import UserDict

import numpy as np
from astropy import wcs
from astropy.io import fits

from chimera.core.exceptions import ChimeraException
from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.sextractor import SExtractor

log = logging.getLogger(__name__)


class WCSNotFoundException(ChimeraException):
    pass


class ImageUtil:
    @staticmethod
    def format_date(datetime):
        if isinstance(datetime, float):
            datetime = dt.datetime.fromtimestamp(datetime)

        return datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @staticmethod
    def make_filename(
        path="$DATE-$TIME", subs={}, date_format="%Y%m%d", time_format="%H%M%S"
    ):
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
        local_time = dt.datetime.now()
        utc_time = dt.datetime.utcnow()

        if local_time.hour < 12:
            jd_day = local_time - dt.timedelta(days=1)
        else:
            jd_day = local_time

        subs_dict = {
            "LAST_NOON_DATE": jd_day.strftime(date_format),
            "DATE": utc_time.strftime(date_format),
            "TIME": utc_time.strftime(time_format),
        }

        # add any user-specific keywords
        subs_dict.update(subs)

        dir_name, file_name = os.path.split(path)
        dir_name = os.path.expanduser(dir_name)
        dir_name = os.path.expandvars(dir_name)
        dir_name = os.path.realpath(dir_name)

        base_name, ext = os.path.splitext(file_name)
        if not ext:
            ext = "fits"
        else:
            ext = ext[1:]

        dir_name = string.Template(dir_name).safe_substitute(subs_dict)
        base_name = string.Template(base_name).safe_substitute(subs_dict)
        ext = string.Template(ext).safe_substitute(subs_dict)

        final_name = os.path.join(dir_name, f"{base_name}{os.path.extsep}{ext}")

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        if not os.path.isdir(dir_name):
            raise OSError(
                f"A file with the same name as the desired directory already exists. ('{dir_name}')"
            )

        if os.path.exists(final_name):
            base, ext = os.path.splitext(final_name)
            i = 1
            while os.path.exists(f"{base}-{i:03d}{ext}"):
                i += 1
                if i == 1000:
                    raise
        dir_name = os.path.realpath(dir_name)

        base_name, ext = os.path.splitext(file_name)
        if not ext:
            ext = "fits"
        else:
            # remove first dot
            ext = ext[1:]

        # make substitutions
        dir_name = string.Template(dir_name).safe_substitute(subs_dict)
        base_name = string.Template(base_name).safe_substitute(subs_dict)
        ext = string.Template(ext).safe_substitute(subs_dict)

        final_name = os.path.join(dir_name, f"{base_name}{os.path.extsep}{ext}")

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        if not os.path.isdir(dir_name):
            raise OSError(
                f"A file with the same name as the desired directory already exists. ('{dir_name}')"
            )

        # If filename exists, append -NNN to the end of the file name.
        # A maximum of 1000 files can be generated with the same filename.
        if os.path.exists(final_name):
            base, ext = os.path.splitext(final_name)
            i = 1
            while os.path.exists(f"{base}-{i:03d}{ext}"):
                i += 1
                if i == 1000:
                    raise OSError(
                        f"Reached the maximum of 999 files with the same name ({final_name})."
                    )

            final_name = f"{base}-{i:03d}{ext}"

        return final_name

    @staticmethod
    def download(image, out_file=None, overwrite=False, max_attempts=2):
        """
        Downloads the image from imageServer http to localfile.
        :param image: Image object to download
        :param out_file: Output filename
        :param overwrite: If True, overwrites existing file
        :param max_attempts: Number of maximum attempts to download
        :return: True if ok, False otherwise
        """
        if out_file is None:
            out_file = image.filename
        if overwrite is False and os.path.exists(out_file):
            return True
        attempts = 0
        while attempts < max_attempts:
            try:
                response = urllib.request.urlopen(image.http())
                content = response.recv()
                f = open(out_file, "wb")
                f.write(content)
                f.close()
                return True
            except urllib.error.URLError:
                attempts += 1
        return False


class Image(UserDict):
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

    def url(self):
        return f"file://{self.filename},{self.http()}"

    @staticmethod
    def from_url(url, fix=False, mode="readonly"):
        url_parts = url.split(",")
        if url_parts[0].startswith("file://"):
            # try local file first
            filename = url_parts[0][7:]
            if os.path.exists(filename):
                return Image.from_file(filename, fix=fix, mode=mode)
            # try http next
            elif len(url_parts) >= 2 and url_parts[1].startswith("http"):
                http_url = url_parts[1]
                return Image.from_file(http_url, fix=fix, mode=mode)
        return None

    @staticmethod
    def from_file(filename, fix=False, mode="update"):
        fd = fits.open(filename, mode=mode)
        if "http" in filename:
            filename = os.path.basename(filename)
        img = Image(filename, fd)

        if fix:
            img.fix()

        return img

    @staticmethod
    def create(data, image_request=None, filename=None):
        if image_request:
            try:
                filename = image_request["filename"]
            except KeyError:
                if not filename:
                    raise TypeError(
                        "Invalid filename, you must pass filename=something"
                        "or a valid ImageRequest object"
                    )

        filename = ImageUtil.make_filename(filename)

        headers = [
            (
                "DATE",
                ImageUtil.format_date(dt.datetime.utcnow()),
                "date of file creation",
            ),
            ("AUTHOR", "Chimera", "author of the data"),
            ("FILENAME", os.path.basename(filename), "name of the file"),
        ]

        hdu = fits.PrimaryHDU()
        # TODO: Implement BITPIX support
        hdu.scale("int16", "", bzero=32768, bscale=1)

        if image_request:
            headers += image_request.headers

            for h in headers:
                try:
                    hdu.header.set(*h)
                except Exception as e:
                    log.warning(f"Couldn't add {str(h)}: {str(e)}")

            if image_request["compress_format"] == "fits_rice":
                filename = os.path.splitext(filename)[0] + ".fz"
                img = fits.CompImageHDU(
                    data=data, header=hdu.header, compression_type="RICE_1"
                )
                img.writeto(filename, checksum=True)
                return Image.from_file(filename)

        hdu.data = data

        hdu_list = fits.HDUList([hdu])
        hdu_list.writeto(filename)
        hdu_list.close()

        del hdu_list
        del hdu

        return Image.from_file(filename)

    #
    # standard constructor
    #
    def __init__(self, filename, fd):
        UserDict.__init__(self)

        self._fd = fd
        self._filename = filename
        self._http = None
        self._wcs = None
        self._id = uuid.uuid4().hex

    @property
    def filename(self):
        return self._filename

    @property
    def id(self):
        return self._id

    def close(self):
        self._fd.close()

    def http(self, http=None):
        if http:
            self._http = http
        return self._http

    def __str__(self):
        return f"<Image {self.filename}>"

    #
    # serialization support
    # we close before pickle and reopen after it
    #
    def __getstate__(self):
        if self._fd:
            self._fd.close()
            self._fd = None
        return self.__dict__

    def __setstate__(self, args):
        self.__dict__ = args
        self._fd = fits.open(self._filename, mode="update")

    #
    # geometry
    #

    def width(self):
        return self["NAXIS1"]

    def height(self):
        return self["NAXIS2"]

    def size(self):
        return (self.width(), self.height())

    def center(self):
        return (self.width() / 2.0, self.height() / 2.0)

    #
    # WCS
    #
    def pixel_at(self, *world):
        if not self._find_wcs():
            return (0, 0)

        pixel = self._value_at(self._wcs.wcs_world2pix, *world)

        # round pixel to avoid large decimal numbers and get out strange -0
        pixel = list(round(p, 6) for p in pixel)

        if pixel[0] == (-0.0):
            pixel[0] = 0.0
        if pixel[1] == (-0.0):
            pixel[1] = 0.0

        return tuple(pixel)

    def world_at(self, *pixel):
        if not self._find_wcs():
            return Position.from_ra_dec(0, 0)

        world = self._value_at(self._wcs.wcs_pix2world, *pixel)
        return Position.from_ra_dec(Coord.from_d(world[0]), Coord.from_d(world[1]))

    def world_at_center(self):
        return self.pixel_at(self.center())

    def _find_wcs(self):
        if not self._wcs:
            try:
                self._wcs = wcs.WCS(self._fd["PRIMARY"].header)
            except (KeyError, ValueError) as e:
                raise WCSNotFoundException(
                    f"Couldn't find WCS information on {self._filename} ('{e}')"
                )

        return True

    def _value_at(self, fn, *coords):
        """
        Accepts a function callback and variable coords.

        If len(coords) == 1 convert (from tuple or Position) to decimal degress.
        If len(coords) == 2, convert (from number or Coord) to decimal degress
        """

        assert len(coords) >= 1
        assert self._wcs is not None

        if len(coords) == 2:
            c1 = Coord.from_h(coords[0]).deg
            c2 = Coord.from_d(coords[1]).deg
        else:
            if isinstance(coords[0], Position):
                c1, c2 = coords[0].dd()
            else:  # assumes as tuple
                c1, c2 = coords[0]

        value = fn(np.array([[c1, c2]]), 1)

        if len(value) >= 1:
            return tuple(value[0])
        else:
            raise WCSNotFoundException("Couldn't convert coordinates.")

    #
    # Source extraction
    #
    def extract(self, params={}, save_catalog=False, save_config=False):
        sex = SExtractor()

        # default params
        sex.config["PIXEL_SCALE"] = 0.45
        sex.config["BACK_TYPE"] = "AUTO"
        sex.config["SATUR_LEVEL"] = 60000
        sex.config["DETECT_THRESH"] = 3.0
        sex.config["VERBOSE_TYPE"] = "QUIET"
        sex.config["PARAMETERS_LIST"] = [
            "NUMBER",
            "XWIN_IMAGE",
            "YWIN_IMAGE",
            "FLUX_BEST",
            "FWHM_IMAGE",
            "FLAGS",
        ]

        # update values from user params
        sex.config.update(params)

        # ok, here we go!
        try:
            sex.run(self._filename, clean=False)
            result = sex.catalog()
            return result
        finally:
            if save_catalog:
                shutil.move(sex.config["CATALOG_NAME"], save_catalog)
            if save_config:
                shutil.move(sex.config["CONFIG_FILE"], save_config)

            sex.clean(config=True, catalog=True, check=True)

    #
    # I/O and verification
    #
    def fix(self):
        self._fd.verify("fix")

    def save(self, filename=None, verify="exception"):
        if filename:
            self._fd.writeto(filename, output_verify=verify)
        else:
            self._fd.flush(output_verify=verify)

        return True

    def _do_compress(self, filename, format):
        if format.lower() == "bz2":
            bz_filename = filename + ".bz2"
            try:
                with open(filename, "rb") as raw_fp:
                    with bz2.BZ2File(bz_filename, "wb", compresslevel=4) as bz_fp:
                        # Read in chunks to avoid memory issues with large files
                        while True:
                            chunk = raw_fp.read(8192)  # 8KB chunks
                            if not chunk:
                                break
                            bz_fp.write(chunk)
                os.unlink(filename)
            except Exception:
                # Clean up compressed file if compression failed
                if os.path.exists(bz_filename):
                    os.unlink(bz_filename)
                raise
        elif format.lower() == "gzip":
            gz_filename = filename + ".gz"
            try:
                with open(filename, "rb") as raw_fp:
                    with gzip.GzipFile(gz_filename, "wb", compresslevel=5) as gz_fp:
                        # Read in chunks to avoid memory issues with large files
                        while True:
                            chunk = raw_fp.read(8192)  # 8KB chunks
                            if not chunk:
                                break
                            gz_fp.write(chunk)
                os.unlink(filename)
            except Exception:
                # Clean up compressed file if compression failed
                if os.path.exists(gz_filename):
                    os.unlink(gz_filename)
                raise
        elif format.lower().startswith("fits_"):
            # compression methods inherent to fits standard, are done when saving image.
            return
        else:  # zip
            zip_filename = filename + ".zip"
            try:
                with open(filename, "rb") as raw_fp:
                    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_fp:
                        # For zip, we need to read all at once due to writestr API
                        zip_fp.writestr(os.path.basename(filename), raw_fp.read())
                os.unlink(filename)
            except Exception:
                # Clean up compressed file if compression failed
                if os.path.exists(zip_filename):
                    os.unlink(zip_filename)
                raise

    def compress(self, format="bz2", multiprocess=False):
        if multiprocess and sys.version_info[0:2] >= (2, 6):
            from multiprocessing import Process

            p = Process(target=self._do_compress, args=(self.filename, format))
            p.start()
            p.join()  # Wait for the process to complete
        else:
            self._do_compress(self.filename, format)

    # dict mixin implementation for headers
    def __getitem__(self, key):
        return self._fd["PRIMARY"].header.__getitem__(key)

    def __setitem__(self, key, value):
        if key not in self:
            self += (key, value)
            return True

        return self._fd["PRIMARY"].header.__setitem__(key, value)

    def __delitem__(self, key):
        return self._fd["PRIMARY"].header.__delitem__(key)

    def keys(self):
        return [item[0] for item in list(self._fd["PRIMARY"].header.items())]

    def items(self):
        return list(self._fd["PRIMARY"].header.items())

    def __contains__(self, key):
        return key in self._fd["PRIMARY"].header

    def __iter__(self):
        yield from self.keys()

    def iteritems(self):
        yield from self.items()

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
