#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.vizquery import VizQuery
from chimera.util.position import Position
from chimera.util.coord import Coord
from chimera.util.catalog import Catalog

class Landolt (VizQuery, Catalog):

    # Landolt inherited VizQuery, its init should be the same as the 
    # parent class.  to do that I call VizQuery.__init__(self)
    def __init__(self):
        VizQuery.__init__(self)

    def getName(self):
        return "Landolt"

    def find (self, near=None, limit=9999, **conditions):

        self.useCat("II/183A/")
        #self.useCat("II/118/")

        if conditions.get("closest", False):
            limit = 1
            self.useColumns("*POS_EQ_RA_MAIN,*POS_EQ_DEC_MAIN,*ID_MAIN,Vmag,_r", sortBy="_r")
        else:
            self.useColumns("*POS_EQ_RA_MAIN,*POS_EQ_DEC_MAIN,*ID_MAIN,Vmag,_r", sortBy="*POS_EQ_RA_MAIN")
        
        if near:
            self.useTarget(near, radius=conditions.get("radius", 45))
        
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
