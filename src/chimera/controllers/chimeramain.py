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

import Pyro.core
import Pyro.naming

import chimera.util.etree.ElementTree as ET
from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.version import _chimera_version_, _chimera_description_


class Site(object):

    def __init__(self, args = []):

        self.options, self.args = self.parseArgs(args)

        # verbosity level
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(module)s:%(lineno)d %(message)s',
                            datefmt='%d-%m-%Y %H:%M:%S (%j)')

        if self.options.verbose == 1:
            logging.getLogger().setLevel(logging.INFO)

        if self.options.verbose > 1:
            logging.getLogger().setLevel(logging.DEBUG)

        self.manager = None

        logging.info("Starting system.")

    def parseArgs(self, args):

        def check_location (option, opt_str, value, parser):
            l = Location (value)
            
            if not value or not l.isValid ():
                raise optparse.OptionValueError ("%s requires a valid location (%s passed)." % (opt_str, value))

            eval ('parser.values.%s.append ("%s")' % (option.dest, value))

        def check_includepath (option, opt_str, value, parser):

            if not value or not os.path.isdir (os.path.abspath(value)):
                raise optparse.OptionValueError ("%s requires a valid directory (%s doesn't exists)." % (opt_str, os.path.abspath(value)))

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

        parser.add_option("-f", "--file", action="append", dest="config",
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

        parser.add_option("-v", "--verbose", action="count", dest='verbose',
                          help="Increase log level (multiple v's to increase even more).")

        parser.set_defaults(instruments = [],
                            controllers = [],
                            drivers     = [],
                            config = [],
                            inst_dir = [],
                            ctrl_dir = [],
                            drv_dir = [],
                            verbose = 0)

        return parser.parse_args(args)

    def init(self):

        # manager
        self.manager = Manager(addr=("150.162.110.2", 9876))

        # config file
        self.config = SiteConfiguration()
        
        for config in self.options.config:
            self.config.read(config)

        # directories

        for _dir in self.options.inst_dir:
            self.manager.appendPath("instrument", _dir)
    
        for _dir in self.options.ctrl_dir:
            self.manager.appendPath("controller", _dir)
        
        for _dir in self.options.drv_dir:
            self.manager.appendPath("driver", _dir)

        # init from config

        for drv in self.config.getDrivers():
            self.manager.startDriver(drv)

        for inst in self.config.getInstruments():
            self.manager.startInstrument(inst)

        for ctrl in self.config.getControllers():
            self.manager.startController(ctrl)

        # init from cmd line
        for drv in self.options.drivers:
            self.manager.startDriver(drv)

        for inst in self.options.instruments:
            self.manager.startInstrument(inst)
            
        for ctrl in self.options.controllers:
            self.manager.startController(ctrl)


    def shutdown(self):
        self.manager.shutdown()
        logging.debug("Shutting down system.")
