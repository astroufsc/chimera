
from chimera.util.image import Image

from chimera.util.coord    import Coord
from chimera.util.position import Position

class TestImage (object):

    def test_headers (self):

        img = Image.fromFile("teste-sem-wcs.fits", fix=False)

        print
        
        for k, v in img.items():
            print k,v, type(v)

        #img += ("TEST", 10, "test header")
        #img.save()

    def test_wcs (self):

        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:
            img = Image.fromFile(f, fix=False)

            print f
            world =  img.worldAt(0,0)
            print "world value at pixel 0,0:", world
            print "pixel value at world %s:" % world, img.pixelAt(world)
            print "world value at center pix %s:" % str(img.center), img.worldAt(img.center)
            print

    def test_extractor (self):

        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:
            img = Image.fromFile(f, fix=False)

            stars = img.extract()

            print
            print "Found %d star(s) on image %s, showing first 10:" % (len(stars), img.filename)

            for star in stars[:10]:
                print star["NUMBER"], star["XWIN_IMAGE"], star["YWIN_IMAGE"], star["FLUX_BEST"]
        
        
