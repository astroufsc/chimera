
from ucac2 import UCAC2
from ppm import PPM

class TestCatalog (object):

    def test_closest (self):

        for catalog in [UCAC2, PPM]:

            cat = catalog()
            data = cat.find(near="15:18:33.7 +02:04:58", closest=True)

            assert data.nrows == 1

    
    def test_box (self):

	print

        for catalog in [UCAC2, PPM]:

            cat = catalog()
            data = cat.find(near="15:18:33.7 +02:04:58", box=3600)

            assert data.nrows > 0
            print data.nrows

