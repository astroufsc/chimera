#! /usr/bin/python
# -*- coding: iso8859-1 -*-

import sys
import logging

import uts.util.etree.ElementTree as ET
from xml.parsers.expat import ExpatError, ErrorString

class SiteConfiguration(object):

    def __init__(self):

        self.__sites = []
        self.__instruments = []
        self.__controllers = []
        self.__drivers     = []

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
        
        # ok, let's go!
        # FIXME: refactor (tá na cara o que fazer... o código está todo repetido)

        # sites (ok, just one site makes sense by now, but we can expand this later)
        sites = root.findall("site")
        
        for site in sites:

            tmpSite = {}
            tmpSite["name"]      = site.get("name", "UFSC")
            tmpSite["latitude"]  = site.get("latitude", "0")
            tmpSite["longitude"] = site.get("longitude", "0")
            tmpSite["altitude"]  = site.get("altitude", "0")

            self.__sites.append(tmpSite)

        # get all instruments
        insts = root.findall("instruments/instrument")

        for inst in insts:
            tmpInst = {}
            tmpInst["name"]    = inst.get("name", "inst" + str(len(self.__instruments) + 1))
            tmpInst["class"]   = inst.get("class", object)
            tmpInst["options"] = []

            # get all options
            opts = inst.findall("option")

            for opt in opts:
                tmpOpt = {}
                tmpOpt["name"]  = opt.get("name")
                tmpOpt["value"] = opt.get("value")

                tmpInst["options"].append(tmpOpt)
                

            self.__instruments.append(tmpInst)

        ctrls = root.findall("controllers/controller")

        for ctrl in ctrls:

            tmpCtrl = {}
            tmpCtrl["name"]    = ctrl.get("name", "ctrl" + str(len(self.__controllers) + 1))
            tmpCtrl["class"]   = ctrl.get("class", object)
            tmpCtrl["options"] = []

            # get all options
            opts = ctrl.findall("option")

            for opt in opts:
                tmpOpt = {}
                tmpOpt["name"]  = opt.get("name")
                tmpOpt["value"] = opt.get("value")

                tmpCtrl["options"].append(tmpOpt)

            self.__controllers.append(tmpCtrl)


        # get all drivers
        drvs = root.findall("drivers/driver")

        for drv in drvs:
            tmpDrv = {}
            tmpDrv["name"]    = drv.get("name", "drv" + str(len(self.__drivers) + 1))
            tmpDrv["class"]   = drv.get("class", object)
            tmpDrv["options"] = []

            # get all options
            opts = inst.findall("option")

            for opt in opts:
                tmpOpt = {}
                tmpOpt["name"]  = opt.get("name")
                tmpOpt["value"] = opt.get("value")

                tmpDrv["options"].append(tmpOpt)
                
            self.__drivers.append(tmpDrv)

    def dump(self):

        def printIt(l):
            s = "%s (%s)\n" % (l["name"], l["class"])
            print s,"="*len(s)
            print
            
            for opt in l["options"]:
                print "%s = %s" % (opt["name"], opt["value"])

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



if __name__ == '__main__':

    import sys

    if(len(sys.argv) > 1):
        
        conf = SiteConfiguration()
        conf.read(sys.argv[1])
        conf.dump()
    
