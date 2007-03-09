#! /usr/bin/python
# -*- coding: iso8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from types import FloatType, IntType, StringType

import re
import math

class Coord(object):

    """
    Coordenada angular

    A coordenada e armazenada em um float. Metdos convertem a coordenada para as diferentes representacoes.

    O construtor utiliza um parser que e capaz de identificar os seguintes formatos de coordenadas:

    100		(int ou str)   decimal ou radiano
    100.09	(float ou str) decimal ou radiano
     10 00 00	(str) horario ou sexagesimal
    +10 00 00.0	(str) horario ou sexagesimal
     10:00:00.0	(str) horario ou sexagesimal

     SIMBAD examples:
      20 54 05.689 +37 01 17.38
      10:12:45.3-45:17:50
      15h17m-11d10m
      15h17+89d15
      275d11m15.6954s+17d59m59.876s
      12.34567h-17.87654d
      350.123456d-17.33333d <=> 350.123456 -17.33333

      (not all supported)
    """

    deg2rad = math.pi/180.0
    rad2deg = 180.0/math.pi

    def __init__(self, coord):

        self._coord = self._parse(coord)

    def _parse(self, coord):

        _re = re.compile('(?P<grau>[+-]?[ ]*\d+)[: ]+(?P<min>\d+)[: ]+(?P<seg>\d+\.?\d*)')

        if isinstance(coord, Coord):
            return coord.get()
        
	if type(coord) in [FloatType, IntType]:
		return float(coord)

	if type(coord) == StringType:

            # try to match the regular expression
            matches = _re.search(coord)

            if matches:
                grau, min, seg = matches.groups()

                _coord = abs(float(grau)) + float(min)/60.0 + float(seg)/3600.0

                if float(grau) < 0:
                    _coord = -(_coord)

                return _coord

            # try to convert right to float
            try:
                return float(coord)
            except ValueError:
                return False

        # when everithing fails, returns 0.0
        return 0.0

    def get(self):
        return self._coord

    def sexagesimal(self, dsep = " ", msep=""):
        msep = msep or dsep
        
        return self._str(dsep, msep, 1.0)

    def hor(self, hsep = " ", msep = ""):
        msep = msep or hsep
        
        return self._str(hsep, msep, 15.0)

    def _str(self, sep1 = " ", sep2 = " ", factor = 1.0):

        coord = abs(self.get())/factor
        
        _grau = int(coord)
        _min  = (coord - _grau) * 60
        _seg  = (_min - int(_min)) * 60

        _min = int(_min)

        if self.get() < 0:
            _grau = -(_grau)

        return '%02d%s%02d%s%02.2f' % (_grau, sep1, _min, sep2, _seg)

    def rad(self):
        return self.get() * Coord.deg2rad

    def arcsec(self):
        return self.get() * 3600.0

    def decimal(self):
        return self.get()

    def __str__(self):
        return self.sexagesimal()

    def __repr__(self):
        return str(self.get())

    def __add__(self, other):
        # other could be int, float, str or another Coord
        # we use _parse to transform whatever __add__ gets to a float and then we do our work

        other = self._parse(other)

        return Coord(self.get() + other)

    def __sub__(self, other):
        other = self._parse(other)

        return Coord(self.get() - other)

    def __mul__(self, other):
        return Coord(self.get()*other)

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __iadd__(self, other):

        other = self._parse(other)

        self._coord = self.get() + other

        return self

    def __isub__(self, other):

        other = self._parse(other)

        self._coord = self.get() - other

        return self

    def __imul__(self, other):
        self._coord = self.get() * other
        
        return self

    def __lt__(self, other):
        other = self._parse(other)

        return self.get() < other

    def __le__(self, other):
        other = self._parse(other)
        
        return self.get() <= other
                    
    def __eq__(self, other):
        other = self._parse(other)

        return self.get() == other

    def __ne__(self, other):
        other = self._parse(other)
        
        return self.get() != other

    def __gt__(self, other):
        other = self._parse(other)
        
        return self.get() > other

    def __ge__(self, other):
        other = self._parse(other)

        return self.get() >= other

                    
class Ra(Coord):
    def __init__(self, coord):
        
        Coord.__init__(self, coord)

        # convert from hours to degrees
        self._coord = self.get() * 15.0

    def __str__(self):
        return self.hor()


class Dec(Coord):
    def __init__(self, coord):
        Coord.__init__(self, coord)

    def __str__(self):
        return self.sexagesimal()

class Az(Coord):
    def __init__(self, coord):
        Coord.__init__(self, coord)

    def __str__(self):
        return self.decimal()

class Alt(Coord):
    def __init__(self, coord):
        Coord.__init__(self, coord)

    def __str__(self):
        return self.decimal()

class Lat(Coord):
    def __init__(self, coord):
        Coord.__init__(self, coord)

    def __str__(self):
        return self.sexagesimal()

class Long(Coord):
    def __init__(self, coord):
        Coord.__init__(self, coord)

    def __str__(self):
        return self.sexagesimal()
    
class Point(object):

    def __init__(self, ra, dec):

        if isinstance(ra, Coord):
            self.ra = ra
        else:
            self.ra = Ra(ra)

        if isinstance(dec, Coord):
            self.dec = dec
        else:
            self.dec = Dec(dec)

    def __str__(self):
        return "%s %s" % (self.ra, self.dec)

    def _dist(self, obj, r = False):

        xr1 = self.ra.rad()
        yr1 = self.dec.rad()

        cosb = math.cos (yr1)
        pos10 = math.cos (xr1) * cosb
        pos11 = math.sin (xr1) * cosb
        pos12 = math.sin (yr1)

        xr2 = obj.ra.rad()
        yr2 = obj.dec.rad()
        
        cosb = math.cos (yr2)
        pos20 = math.cos (xr2) * cosb
        pos21 = math.sin (xr2) * cosb
        pos22 = math.sin (yr2)

        # /* Modulus squared of half the difference vector */
        w = 0.0
        w = w + (pos10 - pos20) * (pos10 - pos20)
        w = w + (pos11 - pos21) * (pos11 - pos21)
        w = w + (pos12 - pos22) * (pos12 - pos22)
        
        w = w / 4.0
        if (w > 1.0): w = 1.0

        # /* Angle beween the vectors */
        diff = 2.0 * math.atan2 (math.sqrt (w), math.sqrt (1.0 - w))
        diff = diff * Coord.rad2deg

        return diff*3600

    def _distp(self, obj):

        _ra  = (obj.ra.decimal() - self.ra.decimal())
        _ra *= self._cosdeg(0.5*(obj.dec.decimal() - self.dec.decimal()))
        
        _dec = (obj.dec.decimal() - self.dec.decimal())

        return Point(_ra/15.0, _dec)

    def _cosdeg(self, angle):
        resid = abs(angle % 360.0)

        if resid == 0.0:
            return 1.0
        elif resid == 90.0:
            return 0.0
        elif resid == 180.0:
            return -1.0
        elif resid == 270.0:
            return 0.0

        return math.cos(angle*Coord.deg2rad)
            
    def dist(self, obj):
        return self._dist(obj)

    def distp(self, obj):
	return self._distp(obj)

    def near(self, other, dist):

        d = self.dist(other)

        # distance could be in simple float/int arcsec or another Coord object
        dist = Coord(dist)

        return d <= dist.arcsec()

if __name__ == '__main__':
    #     m5 = Point("15 18 33.75", "+02 04 57.7")
    #     m51 = Point("13 29 52.37", "+47 11 40.8")

    #     print m5
    #     print m51

    #     print m5.dist(m51)
    #     print m5.distp(m51)

    #a = Point("00:00:00", "00:00:00")
    #b = Point("12:00:00", "45:00:00")

    #print a.dist(b)

    #    v = a.distp(b)
    #print v.ra.arcsec(), v.dec.arcsec()

    #    print a
    #    print b
    
    #    print a + v

    
    siriusA = Point("06 45 08.9173", "-16 42 58.017")
    #siriusB = Point("06 45 09", "-16 43 06")
    #siriusC = Point("06 45 06", "-16 42 00")

    #print siriusA.dist(siriusB)
    #print siriusA.dist(siriusC)

    #print siriusA.near(siriusB, '00 00 08.1')
    #print siriusA.near(siriusB, '00 01 30') 

    print siriusA.ra.hor("h ", "m ")
    print siriusA.dec.sexagesimal("* ","' ") 
