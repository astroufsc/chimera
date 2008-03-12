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


import logging
import random

from xml.parsers.expat import ExpatError, ErrorString

import chimera.util.etree.ElementTree as ET

import chimera.core.log
from chimera.core.location import Location

log = logging.getLogger(__name__)


class SiteConfig (object):

    def __init__(self):
        self.__sites = []
        self.__chimera = {"host": None, "port": None}
        self.__instruments = []
        self.__controllers = []
        self.__drivers     = []

    def getChimera (self):
        return self.__chimera
    
    def getInstruments(self):
        return self.__instruments

    def getControllers(self):
        return self.__controllers

    def getSites(self):
        return self.__sites

    def getDrivers(self):
        return self.__drivers
        
    def read(self, config):
        self._read(config)

    def _read(self, config):

        try:
            root = ET.parse(config)
            
        except IOError, e:
            logging.error("Error opening %s (%s)." % (config, e.strerror))
            return False

        except ExpatError, e:
            logging.error("Error parsing %s config at line %s column %s (%s)." % (config,
                                                                                  e.lineno,
                                                                                  e.offset,
                                                                                  ErrorString(e.code)))
            return False
        
        # chimera (hostname/port config)
        chimera = root.getroot()
        self.__chimera["host"] = chimera.get("host", None)
        try:
            self.__chimera["port"] = int(chimera.get("port", None))
        except ValueError:
            log.warning("Invalid port configuration. Using default port.")
        except TypeError:
            self.__chimera["port"] = None
        
        # sites (ok, just one site makes sense by now, but we can expand this later)
        sites = root.findall("site")
        
        for site in sites:
            
            tmpSite = {}
            
            tmpSite["name"]      = site.findtext("name", "UFSC")
            tmpSite["latitude"]  = site.findtext("latitude", "0")
            tmpSite["longitude"] = site.findtext("longitude", "0")
            tmpSite["altitude"]  = site.findtext("altitude", "0")

            try:
                tmpSite["utc_offset"]  = int(site.findtext("utc_offset", 0))
            except ValueError:
                tmpSite["utc_offset"]  = 0
                
            dst = site.find("dst")
            if dst and len(dst) > 0:
                tmpSite["dst"] = True
            else:
                tmpSite["dst"] = False
                
            self.__sites.append(tmpSite)

        # instruments
        insts = root.findall("instruments/instrument")
        self.__instruments = self._parseSection (insts)

        # controllers
        ctrls = root.findall("controllers/controller")        
        self.__controllers = self._parseSection (ctrls)

        # get all drivers
        drvs = root.findall("drivers/driver")
        self.__drivers = self._parseSection (drvs)

    def _parseSection (self, entries):

        ret = []

        for entry in entries:
            tmpEntry = {}
            tmpEntry["host"]   = entry.get("host", None)
            tmpEntry["port"]   = entry.get("port", None)
            tmpEntry["cls"]    = entry.get("class", None)
            tmpEntry["name"]   = entry.get("name", "%s-%d" % (tmpEntry["cls"], random.randint(1, 1e9)))
            tmpEntry["config"] = {}

            # get all options
            opts = entry.findall("option")

            for opt in opts:
                tmpKey   = opt.get("name")
                tmpValue =  opt.get("value")
                tmpEntry["config"][tmpKey] = tmpValue

            loc = Location(**tmpEntry)
            ret.append(loc)

        return ret

    def dump(self):

        def printIt(l):
            s = "%s (%s)\n" % (l["name"], l["cls"])
            print s,"="*len(s)
            print
            
            for k,v in l["options"].items():
                print "%s = %s" % (k, v)

            print

        def printSite(l):
            s = "%s (lat. %s, long. %s, alt. %s)\n" % (l["name"],
                                                      l["latitude"],
                                                      l["longitude"],
                                                      l["altitude"])
            print s,"="*len(s)
            print
            
        for s in self.__sites:
            printSite(s)

        for i in self.__instruments:
            printIt(i)

        for c in self.__controllers:
            printIt(c)

        for d in self.__drivers:
            printIt(d)

