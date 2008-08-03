#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

class Catalog (object):

    def getName (self):
        """
        Return the catalog name
        """

    def getMetadata (self):
        """
        Returns a list of tuples with information about the each
        column of the catalog.  Each tuple contains, in this order,
        name of the column, unit of the column data and a comment.
        """

    def getMagnitudeBands (self):
        """
        Return a list of the available magnitude bands on this catalog
        """
   
    def find (self, near, limit=None, **conditions):
        """
        Query the catalog near a specific object/place with spatial
        and flux limits.
        
        Examples:

        ucac = Catalog()

        ucac.find (near='00:00:00 +00:00:00', radius=10)
        ucac.find (near='m5', box=(240, 240))           
        ucac.find (near='m4', radius=10, magV=10, limit=1)
        ucac.find (near='meridian', magV=(10, 12), limit=10)                  

        Keywords:

        closest (bool)
        =====================
        return the closest star near the given coordinate independent
        of radius and box limits. (it's ortogonal to box/radius
        options).

        near (str)
        ======================

        name (resolved by any resolver), ra dec pair in degress or
        sexagesimal, special names (meridian, zenith)

        radius (int)
        ==========

        limit selection to r arseconds from target (r can be arcsec or
        degress)

        box (int or tuple of 2 ints)
        ================

        limit to a box centered on the target with w arcsec (or
        degresss) in increasing right ascension direction and h
        arseconds towards the north (or degress)

        limit (int)
        =========

        max number of objects to return (default = 100)

        magX (float | tuple of 2 floats)
        ================================

        Limit the query based on the X magnitude. One float N param
        was given, limit the query to the Nth faintest magnitude (only
        stars brighter than N will be returned).

        If a tuple (B, F) was given, limit the query to stars brighter
        than F but fainter than B.


        Unknown keywords will be ignored (properly warned on the log).

        """
