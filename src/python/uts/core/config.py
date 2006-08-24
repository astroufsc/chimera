#! /usr/bin/python
# -*- coding: iso8859-1 -*-

import sys
import logging

import uts.util.etree.ElementTree as ET

class SiteConfiguration(object):

    def __init__(self):

        self.__sites = []
        self.__instruments = []
        self.__controllers = []

    def getInstruments(self):

        return self.__instruments

    def getControllers(self):

        return self.__controllers

    def getSites(self):

        return self.__sites

    def read(self, config):

        self._read(config)

    def _read(self, config):

        try:

            root = ET.parse(config)
            
        except IOError, e:

            logging.exception("Error opening %s" % config)
            return False

        # ok, let's go!

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


    def dump(self):
        for i in self.__instruments:
            print i

        for c in self.__controllers:
            print c

        for s in self.__sites:
            print s


if __name__ == '__main__':

    import sys

    if(len(sys.argv) > 1):
        
        conf = SiteConfiguration()
        conf.read(sys.argv[1])
        conf.dump()
    
