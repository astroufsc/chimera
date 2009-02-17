#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

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

from chimera.util.position import Position

import chimera.util.etree.ElementTree as ET
from chimera.core.exceptions import ObjectNotFoundException

import chimera.core.log

#import suds
#suds.logger('suds').setLevel(logging.DEBUG)

from suds.xsd.sxbasic import Import
Import.bind('http://schemas.xmlsoap.org/soap/encoding/')

from suds.client import Client

class Simbad (object):

    WSDL = 'http://cdsws.u-strasbg.fr/axis/services/Sesame?wsdl'
    
    def __init__ (self):
        self.client = Client(Simbad.WSDL)

    def lookup (self, name):
        res = self.client.service.Sesame.sesame(name, 'x', True)
        target = self._parseSesame(res)

        if not target:
            raise ObjectNotFoundException("Cound't found %s on SIMBAD" % name)
        
        return target

    def _parseSesame (self, xml):
       
        sesame = ET.fromstring(xml.replace("&", "&amp;"))

        target = sesame.findall("Target")
        if target:
            for resolver in target[0].findall("Resolver"):
                jpos  = resolver.find("jpos")
                if jpos is None:
                    continue

                return Position.fromRaDec(*jpos.text.split())

        return False
        
if __name__ == '__main__':

    s = Simbad()

    while True:
        try:
            obj = raw_input("Give me an object name: ")
            if obj:
                o = s.lookup(obj)
                if not o: continue
                print o.ra, o.dec
        except (KeyboardInterrupt, EOFError):
            print
            break
