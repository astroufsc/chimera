#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.vizquery import VizQuery
from chimera.util.position import Position
from chimera.util.coord import Coord

class Landolt (VizQuery):

    # Landolt inherited VizQuery, its init should be the same as the 
    # parent class.  to do that I call VizQuery.__init__(self)
    def __init__(self):
        VizQuery.__init__(self)
        

    def find (self, limit=9999):
        """
        @param coords: object coordinates 
        @type  coords: L{Position}
        
        """

        self.useCat("II/183A/")
        #self.useCat("II/118/")
        self.useColumns("*POS_EQ_RA_MAIN,*POS_EQ_DEC_MAIN,*ID_MAIN,Vmag,_r",
                        sortBy="*POS_EQ_RA_MAIN")
        # self.useTarget(Position.fromRaDec("14:00:00","-22:00:00"),radius=45)
        # self.useTarget(coords,radius=45)
        
        x = super(Landolt,self).find(limit)

        for i in x:
            RA = i.pop("*POS_EQ_RA_MAIN")
            i["RA"] = Coord.fromHMS(str(RA))
            DEC = i.pop("*POS_EQ_DEC_MAIN")
            i["DEC"] = Coord.fromDMS(str(DEC))
            ID = i.pop("*ID_MAIN")
            i["ID"] = str(ID)
            V = i.pop("Vmag")
            i["V"] = str(V)
            i.pop("_r")

        return x 
