#! /usr/bin/python
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


import sys
import os.path
import logging
import optparse
from xml.parsers.expat import ExpatError, ErrorString

import chimera.util.etree.ElementTree as ET

from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.version import _chimera_version_, _chimera_description_
from chimera.controllers.site.config import SiteConfig
from chimera.core.exceptions import ChimeraException, printException, InvalidLocationException

from chimera.core.site import Site

import chimera.core.log


log = logging.getLogger(__name__)


class SiteController (object):

    def __init__(self, args = []):

        self.options, self.args = self.parseArgs(args)

        if self.options.verbose == 1:
            chimera.core.log.setConsoleLevel(logging.INFO)
            
        if self.options.verbose > 1:
            chimera.core.log.setConsoleLevel(logging.DEBUG)

        self.manager = None

        self.paths = {"instruments": [],
                      "controllers": [],
                      "drivers": []}

        # add system path
        prefix = os.path.realpath(os.path.join(os.path.abspath(__file__), '../../../'))
        self.paths["instruments"].append(os.path.join(prefix, 'instruments'))
        self.paths["controllers"].append(os.path.join(prefix, 'controllers'))
        self.paths["drivers"].append(os.path.join(prefix, 'drivers'))

    def parseArgs(self, args):

        def check_location (option, opt_str, value, parser):
            try:
                l = Location (value)
            except InvalidLocationException:
                raise optparse.OptionValueError ("%s isnt't a valid location." % value)

            eval ('parser.values.%s.append ("%s")' % (option.dest, value))

        def check_includepath (option, opt_str, value, parser):

            if not value or not os.path.isdir (os.path.abspath(value)):
                raise optparse.OptionValueError ("Couldn't found %s include path." % value)

            eval ('parser.values.%s.append ("%s")' % (option.dest, value))

        def check_xml (option, opt_str, value, parser):

            if not value or not os.path.exists (os.path.abspath(value)):
                raise optparse.OptionValueError ("Couldn't found %s configuration file." % value)

            eval ('parser.values.%s.append ("%s")' % (option.dest, value))


        parser = optparse.OptionParser(prog="chimera", version=_chimera_version_,
                                       description=_chimera_description_,
                                       usage="chimera --help for more information")

        parser.add_option("-i", "--instrument", action="callback", callback=check_location,
                          dest="instruments", type="string",
                          help="Load the instrument defined by LOCATION."
                               "This option could be setted many times to load multiple instruments.",
                          metavar="LOCATION")

        parser.add_option("-c", "--controller", action="callback", callback=check_location,
                          dest="controllers", type="string",
                          help="Load the controller defined by LOCATION."
                               "This option could be setted many times to load multiple controllers.",
                          metavar="LOCATION")

        parser.add_option("-d", "--driver", action="callback", callback=check_location,
                          dest="drivers", type="string",
                          help="Load the driver defined by LOCATION."
                               "This option could be setted many times to load multiple drivers.",
                          metavar="LOCATION")

        parser.add_option("-f", "--file", action="callback", callback=check_xml,
                          dest="config", type="string",
                          help="Load instruments and controllers defined on FILE."
                               "This option could be setted many times to load inst/controllers from multiple files.",
                          metavar="FILE")

        parser.add_option("-I", "--instruments-dir", action="callback", callback=check_includepath,
                          dest="inst_dir", type="string",
                          help="Append PATH to instruments load path.",
                          metavar="PATH")

        parser.add_option("-C", "--controllers-dir", action="callback", callback=check_includepath,
                          dest="ctrl_dir", type="string",
                          help="Append PATH to controllers load path.",
                          metavar="PATH")

        parser.add_option("-D", "--drivers-dir", action="callback", callback=check_includepath,
                          dest="drv_dir", type="string",
                          help="Append PATH to drivers load path.",
                          metavar="PATH")

        parser.add_option("--dry-run", action="store_true", 
                          dest="dry",
                          help="Only list all configured objects (from command line and configuration files) without starting the system.")

        parser.add_option("-v", "--verbose", action="count", dest='verbose',
                          help="Increase log level (multiple v's to increase even more).")

        parser.set_defaults(instruments = [],
                            controllers = [],
                            drivers     = [],
                            config = [],
                            inst_dir = [],
                            ctrl_dir = [],
                            drv_dir = [],
                            dry=False,
                            verbose = 0)

        return parser.parse_args(args)

    def init(self):


        # config file
        self.config = SiteConfig()
        
        for config in self.options.config:
            self.config.read(config)

        # manager
        if not self.options.dry:
            log.info("Starting system.")
            self.manager = Manager(**self.config.getChimera())

        # add site object
        if not self.options.dry:
            
            sites = self.config.getSites()
            
            for site in sites:
                self.manager.addClass(Site, site["name"], site, True)
            
        # search paths
        log.info("Setting objects include path from command line parameters...")
        for _dir in self.options.inst_dir:
            self.paths["instruments"].append(_dir)
    
        for _dir in self.options.ctrl_dir:
            self.paths["controllers"].append(_dir)
        
        for _dir in self.options.drv_dir:
            self.paths["drivers"].append(_dir)

        # init from config
        log.info("Trying to start drivers...")
        for drv in self.config.getDrivers() + self.options.drivers:

            if self.options.dry:
                print drv
            else:
                self._add(drv, path=self.paths["drivers"], start=True)

        log.info("Trying to start instruments...")
        for inst in self.config.getInstruments()+self.options.instruments:
            
            if self.options.dry:
                print inst
            else:
                self._add(inst, path=self.paths["instruments"], start=True)

        log.info("Trying to start controllers...")                
        for ctrl in self.config.getControllers()+self.options.controllers:
            
            if self.options.dry:
                print ctrl
            else:
                self._add(ctrl, path=self.paths["controllers"], start=True)

        log.info("System up and running.")

        # ok, let's wait manager work
        if not self.options.dry:
            self.manager.wait()

    def _add (self, location, path, start):
        try:
            self.manager.addLocation(location, path, start)
        except ChimeraException, e:
            printException(e)
            
    def shutdown(self):
        log.info("Shutting down system.")
        self.manager.shutdown()

