from chimera.util.image import Image, ImageUtil

import numpy as N
import os


class TestImage(object):

    base = os.path.dirname(__file__)

    def test_headers(self):

        img = Image.fromFile(os.path.join(self.base, "teste-sem-wcs.fits"), fix=False)

        print()

        for k, v in list(img.items()):
            print(k, v, type(v))

    def test_wcs(self):

        img = Image.fromFile(os.path.join(self.base, "teste-com-wcs.fits"), fix=False)
        world = img.worldAt(0, 0)
        print("world value at pixel 0,0:", world)
        print(f"pixel value at world {world}:", img.pixelAt(world))
        print(
            f"world value at center pix {str(img.center())}:",
            img.worldAt(img.center()),
        )
        assert world.ra.D is not None
        assert world.dec.D is not None

    def test_extractor(self):

        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:

            img = Image.fromFile(os.path.join(self.base, f), fix=False)

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
            name = ImageUtil.makeFilename(
                os.path.join(os.path.curdir, "autogen-$OBJECT.fits"),
                subs={"OBJECT": "M5"},
            )
            names.append(name)
            open(name, "w").close()

        for name in names:
            assert os.path.exists(name)
            os.unlink(name)

    def test_create(self):

        img = Image.create(N.zeros((100, 100)), filename="autogen-teste.fits")
        assert os.path.exists(img.filename)
        assert img.width() == 100
        assert img.height() == 100

        os.unlink(img.filename)
