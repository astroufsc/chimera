#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.vizquery import VizQuery
from chimera.util.position import Position
from chimera.util.coord import Coord

class Landolt (object):

    @staticmethod
    def find (limit=9999):
        viz = VizQuery()
        viz.useCat("II/183A/")
        viz.useColumns("*POS_EQ_RA_MAIN,*POS_EQ_DEC_MAIN,*ID_MAIN,Vmag,_r",
                        sortBy="*POS_EQ_RA_MAIN")
        viz.useTarget(Position.fromRaDec("14:00:00","-22:00:00"),radius=45)
        
        return viz.find(limit)
