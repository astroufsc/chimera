
from chimera.util.catalogs.landolt import Landolt
from chimera.util.position import Position

class TestLandolt (object):

    def test_find (self):

        landolt = Landolt()
        landolt.useTarget(Position.fromRaDec("14:00:00","-22:00:00"),radius=45)
        landolt.constrainColumns({"Vmag":"<10"})

        data = landolt.find(limit=5)


        for obj in data:
            for k,v in obj.items():
                print k, v

