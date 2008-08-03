#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.catalog import Catalog
from chimera.util.scat    import SCatWrapper


class UCAC2 (Catalog):

    def __init__ (self):
        Catalog.__init__ (self)

        self.scat = SCatWrapper()

    def getName (self):
        return "UCAC2"

    def getMetadata (self):
        return [("UCAC2_NUM", "arbitrary", "UCAC2 number"),
                ("RA", "h:m:s", "Right Ascension (J2000)"),
                ("DEC", "d:m:s", "Declination (J2000)"),
                ("MAG_J", "mag", "J magnitude (1.2 um) from 2MASS"),
                ("MAG_H", "mag", "H magnitude (1.6 um) from 2MASS") ,
                ("MAG_K", "mag", "Ks magnitude (2.2 um) from 2MASS"),
                ("MAG_UCAC", "mag", "Internal UCAC magnitude (red bandpass)"),
                ("R", "arcsec", "Distance from the target")]

    def getMagnitudeBands (self):
        return ["J", "H", "K", "UCAC"]

    def find (self, near, limit=None, **conditions):

        scat_options = {"catalog"   : "ucac2",
                        "near"      : near or "00:00:00 +00:00:00",
                        "limit"     : limit or 100,
                        "bands"     : self.getMagnitudeBands(),
                        "conditions": conditions,
                        "metadata"  : self.getMetadata(),
                        "env"       : os.environ.update({"UCAC2_PATH": "/home/henrique/catalogs/ucac2/"})}

        # OK, run it!
        data = self.scat.run (scat_options)

        return data


