
from chimera.util.image import Image, ImageUtil

from chimera.util.coord    import Coord
from chimera.util.position import Position
from chimera.util.sextractor import SExtractorException

import numpy as N

import os.path

class TestImage (object):
    
    base = os.path.dirname(__file__)

    def test_headers (self):

        img = Image.fromFile(os.path.join(self.base, "teste-sem-wcs.fits"), fix=False)

        print
        
        for k, v in img.items():
            print k,v, type(v)

        #img += ("TEST", 10, "test header")
        #img.save()

    def test_wcs (self):

        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:
            img = Image.fromFile(os.path.join(self.base, f), fix=False)

            print f
            world =  img.worldAt(0,0)
            print "world value at pixel 0,0:", world
            print "pixel value at world %s:" % world, img.pixelAt(world)
            print "world value at center pix %s:" % str(img.center()), img.worldAt(img.center())
            print

    def test_extractor (self):

        for f in ["teste-com-wcs.fits", "teste-sem-wcs.fits"]:
            
            try:
                img = Image.fromFile(os.path.join(self.base, f), fix=False)

                stars = img.extract()

                print
                print "Found %d star(s) on image %s, showing first 10:" % (len(stars), img.filename)

                for star in stars[:10]:
                    print star["NUMBER"], star["XWIN_IMAGE"], star["YWIN_IMAGE"], star["FLUX_BEST"]
                    
            except SExtractorException:
                print "You don't have SExtractor... try to install it before"
        
    def test_make_filename (self):

        names = []

        for i in range(10):
            name = ImageUtil.makeFilename(os.path.join(os.path.curdir, "autogen-$OBJECT.fits"), subs={"OBJECT": "M5"})
            names.append(name)
            file(name, "w").close()

        print
        for n in names: print n

    def test_create (self):

        img = Image.create(N.zeros((100,100)), filename="autogen-teste.fits")
        print img.width, img.height
        
        
                       
        
