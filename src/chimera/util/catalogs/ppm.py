#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.catalog import Catalog
from chimera.util.scat    import SCatWrapper


class PPM (Catalog):

    def __init__ (self):
        Catalog.__init__ (self)

        self.scat = SCatWrapper()

    def getName (self):
        return "PPM"

    def getMetadata (self):
        return [("PPM_NUM", "arbitrary", "PPM number"),
                ("RA", "h:m:s", "Right Ascension (J2000)"),
                ("DEC", "d:m:s", "Declination (J2000)"),
                ("MAG_J", "mag", "J magnitude (1.2 um) from 2MASS"),
                ("SpTyp", "arbitrary", "Spectral type"),
                ("R", "arcsec", "Distance from the target")]

    def getMagnitudeBands (self):
        return ["V"]

    def find (self, near, limit=None, **conditions):

        scat_options = {"catalog"   : "ppm",
                        "near"      : near or "00:00:00 +00:00:00",
                        "limit"     : limit or 100,
                        "bands"     : self.getMagnitudeBands(),
                        "conditions": conditions,
                        "metadata"  : self.getMetadata(),
                        "env"       : os.environ.update({"PPM_PATH": "/home/henrique/catalogs/"})}

        # OK, run it!
        data = self.scat.run (scat_options)

        return data

