
from chimera.util.catalogs.landolt import Landolt

class TestLandolt (object):

    def test_find (self):

        data = Landolt.find(limit=5)

        for obj in data:
            for k,v in obj.items():
                print k, v
            print
