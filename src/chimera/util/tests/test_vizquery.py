
from chimera.util.vizquery import VizQuery
from chimera.util.position import Position

class TestVizQuery (object):

    def test_find (self):
        x = VizQuery()
        x.useCat("II/183A/")
        x.useColumns("*POS_EQ_RA_MAIN,*POS_EQ_DEC_MAIN,*ID_MAIN,Vmag,_r",
                     sortBy="*POS_EQ_RA_MAIN")
        x.useTarget(Position.fromRaDec("14:00:00","-22:00:00"),radius=45)
        
        data = x.find(limit=5)

        for obj in data:
            for k,v in obj.items():
                print k, v
            print
