
from chimera.util.catalogs.ucac2 import UCAC2
from chimera.util.catalogs.ppm import PPM
from chimera.util.catalogs.landolt import Landolt

class TestCatalog (object):

    def test_closest (self):

        #        for catalog in [UCAC2, PPM, Landolt]:
        for catalog in [Landolt]:

            cat = catalog()
            data = cat.find(near="15:18:33.7 +02:04:58", closest=True)

            #assert data.nrows == 1

    
    def test_box (self):

        print

        #for catalog in [UCAC2, PPM, Landolt]:
        for catalog in [Landolt]:

            cat = catalog()
            data = cat.find(near="15:18:33.7 +02:04:58", box=3600)

            #assert data.nrows > 0
            #print data.nrows

