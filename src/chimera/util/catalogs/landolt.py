#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os

from chimera.util.catalog import Catalog
from chimera.util.position import Position
from chimera.util.coord import Coord


class Landolt (Catalog):

    def __init__ (self):
        Catalog.__init__ (self)
        self.obj = []
        self.readLandoltCatalog()


    def getName (self):
        return "LANDOLT"

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
        return ["V"]

    def find (self, near, limit=None, **conditions):
        for i in self.obj:
            print i["NAME"] , i["RADEC"]


    def readLandoltCatalog(self):
        """
        Reads the Landolt catalog of standard stars
        Returns a dictionary with the standards data
        NAME
        RA
        DEC
        V
        B-V
        U-B
        V-R
        R-I
        e_B-V
        e_U-B
        e_V-R
        e_R-I
        e_V-I
        From the catalog readme file:
          1- 11  A11   ---     Star   *Star Designation
         13- 14  I2    h       RAh     Right Ascension 2000 (hours)
         16- 17  I2    min     RAm     Right Ascension 2000 (minutes)
         19- 20  I2    s       RAs     Right Ascension 2000 (seconds)
             22  A1    ---     DE-     Declination 2000 (sign)
         23- 24  I2    deg     DEd     Declination 2000 (degrees)
         26- 27  I2    arcmin  DEm     Declination 2000 (minutes)
         29- 30  I2    arcsec  DEs     Declination 2000 (seconds)
         33- 38  F6.3  mag     Vmag    V magnitude
         40- 45  F6.3  mag     B-V     B-V color
         47- 52  F6.3  mag     U-B     U-B color
         54- 59  F6.3  mag     V-R     V-R color
         61- 66  F6.3  mag     R-I     R-I color
         68- 73  F6.3  mag     V-I     V-I color
         75- 77  I3    ---   o_Vmag    Number of observations
         79- 81  I3    ---     Nd      Number of nights
         84- 89  F6.4  mag   e_Vmag    Mean error of the Mean Vmag
         91- 96  F6.4  mag   e_B-V     Mean error of the Mean (B-V)
         98-103  F6.4  mag   e_U-B     Mean error of the Mean (U-B)
        105-110  F6.4  mag   e_V-R     Mean error of the Mean (V-R)
        112-117  F6.4  mag   e_R-I     Mean error of the Mean (R-I)
        119-124  F6.4  mag   e_V-I     Mean error of the Mean (V-I)
        """
        stds_catname = os.path.join(os.path.dirname(__file__),
                                    "landoltdata/table2.dat")
        stds_catfile = open(stds_catname)
        for i,star in enumerate(stds_catfile):
            self.obj.insert(i,{})
            self.obj[i]["NAME"] = star[0:11]
            ra = Coord.fromHMS("%s %s %s" %(star[12:14],
                                            star[15:17],star[18:20]))
            dec = Coord.fromDMS("%s%s %s %s" %(star[21],star[22:24],
                                               star[25:27],star[28:30]))
            radec = Position.fromRaDec(ra,dec)
            self.obj[i]["RADEC"] = radec
            self.obj[i]["Vmag"] = float(star[32:38])
