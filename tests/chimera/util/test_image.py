import os
import shutil

import numpy as np
import pytest
from astropy.io import fits

from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.interfaces.camera import Bitpix
from chimera.util.image import Image, ImageUtil


def sextractor_available():
    return any(shutil.which(program) for program in ("sextractor", "sex"))


class TestImage:
    base = os.path.dirname(__file__)

    def test_headers(self):
        img = Image.from_file(os.path.join(self.base, "teste-sem-wcs.fits"), fix=False)

        print()

        for k, v in list(img.items()):
            print(k, v, type(v))

    def test_wcs(self):
        img = Image.from_file(os.path.join(self.base, "teste-com-wcs.fits"), fix=False)
        world = img.world_at(0, 0)
        print("world value at pixel 0,0:", world)
        print(f"pixel value at world {world}:", img.pixel_at(world))
        print(
            f"world value at center pix {str(img.center())}:",
            img.world_at(img.center()),
        )
        assert world.ra.deg is not None
        assert world.dec.deg is not None

    @pytest.mark.skipif(
        not sextractor_available(), reason="SExtractor program not installed"
    )
    def test_extractor(self):
        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:
            img = Image.from_file(os.path.join(self.base, f), fix=False)

            stars = img.extract()

            print()
            print(
                f"Found {len(stars)} star(s) on image {img.filename}, showing first 10:"
            )

            for star in stars[:10]:
                print(
                    star["NUMBER"],
                    star["XWIN_IMAGE"],
                    star["YWIN_IMAGE"],
                    star["FLUX_BEST"],
                )

    def test_make_filename(self):
        names = []

        for i in range(10):
            name = ImageUtil.make_filename(
                os.path.join(os.path.curdir, "autogen-$OBJECT.fits"),
                subs={"OBJECT": "M5"},
            )
            names.append(name)
            open(name, "w").close()

        for name in names:
            assert os.path.exists(name)
            os.unlink(name)

    def test_create(self):
        img = Image.create(np.zeros((100, 100)), filename="autogen-teste.fits")
        assert os.path.exists(img.filename)
        assert img.width() == 100
        assert img.height() == 100

        os.unlink(img.filename)


class TestBitpixIsTheCallersToSet:
    """BITPIX follows the pixels, and only a caller who asks changes it.

    The field used to live on `ImageRequest`, defaulting to uint16, and nothing
    ever read it -- so every frame took the dtype of whatever array a driver
    handed over, and `Image.create`'s one attempt to force int16 ran against an
    HDU that had no data yet and did nothing at all. The request has since lost
    the field (a caller cannot know a camera's ADC depth), and what remains is
    an explicit argument for callers who genuinely want a conversion.
    """

    def _written(self, tmp_path, data, **kwargs):
        img = Image.create(data, filename=str(tmp_path / "bitpix.fits"), **kwargs)
        with fits.open(img.filename) as hdul:
            return hdul[0].header, hdul[0].data

    @staticmethod
    def _native(dtype):
        """FITS is big-endian on disk, so floats read back as `>f4`.

        Byte order is not what any of this is about -- normalize it away rather
        than write assertions that would pass on one architecture and not
        another. (Integers come back native already: astropy applies BZERO and
        hands over a fresh array.)
        """
        return dtype.newbyteorder("=")

    def test_pixels_are_written_as_the_driver_made_them(self, tmp_path):
        header, data = self._written(tmp_path, np.zeros((8, 8), np.uint16))
        assert header["BITPIX"] == 16
        # FITS has no unsigned 16-bit type; this pair *is* uint16 on disk.
        assert header["BZERO"] == 32768
        assert data.dtype == np.uint16

    def test_a_float_frame_stays_float_when_nobody_asks(self, tmp_path):
        """The regression that started this: no silent conversion either way."""
        header, data = self._written(tmp_path, np.zeros((8, 8), np.float32))
        assert header["BITPIX"] == -32
        assert self._native(data.dtype) == np.float32

    def test_an_explicit_bitpix_converts(self, tmp_path):
        header, data = self._written(
            tmp_path, np.full((8, 8), 1000.6, np.float32), bitpix=Bitpix.uint16
        )
        assert header["BITPIX"] == 16
        assert data.dtype == np.uint16
        assert (data == 1001).all()  # rounded, not truncated

    def test_out_of_range_saturates_rather_than_wrapping(self, tmp_path):
        """A pixel past the end of the range is at the end of the range.

        Wrapping would put an above-full-well star at zero, which is worse than
        a saturated one: it is wrong in the opposite direction.
        """
        source = np.array([[-5.0, 0.0, 70000.0]], np.float32)
        _, data = self._written(tmp_path, source, bitpix=Bitpix.uint16)
        assert list(data[0]) == [0, 0, 65535]

    def test_bitpix_may_be_named_as_a_bare_string(self, tmp_path):
        """A config-coerced or bus-marshalled value arrives as its name."""
        header, _ = self._written(
            tmp_path, np.zeros((8, 8), np.float32), bitpix="int32"
        )
        assert header["BITPIX"] == 32

    def test_an_unusable_bitpix_leaves_the_pixels_alone(self, tmp_path):
        """Better a frame in the wrong type than no frame at all."""
        header, data = self._written(
            tmp_path, np.zeros((8, 8), np.float32), bitpix="nonsense"
        )
        assert header["BITPIX"] == -32
        assert self._native(data.dtype) == np.float32

    def test_rice_compression_of_integer_pixels_is_lossless(self, tmp_path):
        """The quiet half of the same bug.

        astropy quantizes *floating-point* input to a compressed HDU
        (`quantize_level=16` by default), so while the fake camera was widening
        its uint16 frames to float32, every `.fz` it wrote came back changed --
        measured at up to 691 ADU per pixel on a full-range frame. Integers go
        through RICE untouched, and this is the gate that keeps them integers.
        """
        rng = np.random.default_rng(0)
        source = (rng.random((64, 64)) * 60000).astype(np.uint16)

        request = ImageRequest(
            filename=str(tmp_path / "rice.fits"), compress_format="fits_rice"
        )
        img = Image.create(source, request)

        with fits.open(img.filename) as hdul:
            restored = hdul[1].data
        assert restored.dtype == np.uint16
        assert (restored == source).all()
