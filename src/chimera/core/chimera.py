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

import sys
import os.path
import logging
import os
import time

# FIXME: support Ctrl+C on Windows (get over signals)
import signal

from optparse import OptionParser
from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.version import _chimera_version_, _chimera_description_

from chimera.core.siteconfig import SiteConfig

#FIXME: better singleton pattern
_chimera_singleton = None

def Chimera (args=[]):

    global _chimera_singleton

    if not _chimera_singleton:
        _chimera_singleton = _Chimera (args)

    return _chimera_singleton

class _Chimera (object):

    def __init__(self, args = []):

        self.options, self.args = self.parseArgs(args)

        # verbosity level
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(module)s:%(lineno)d %(message)s',
                            datefmt='%d-%m-%Y %H:%M:%S (%j)')

        if self.options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.manager = None

        self.pid = os.getpid()

        logging.debug("Starting system.")

    def parseArgs(self, args):

        parser = OptionParser(prog="chimera", version=_chimera_version_,
                              description=_chimera_description_)

        parser.add_option("-i", "--instrument", action="append", dest="instruments",
                          help="Load the instrument defined by LOCATION."
                               "This option could be setted many times to load multiple instruments.",
                          metavar="LOCATION")

        parser.add_option("-c", "--controller", action="append", dest="controllers",
                          help="Load the controller defined by LOCATION."
                               "This option could be setted many times to load multiple controllers.",
                          metavar="LOCATION")

        parser.add_option("-d", "--driver", action="append", dest="drivers",
                          help="Load the driver defined by LOCATION."
                               "This option could be setted many times to load multiple drivers.",
                          metavar="LOCATION")

        parser.add_option("-f", "--file", action="append", dest="config",
                          help="Load instruments and controllers defined on FILE."
                               "This option could be setted many times to load inst/controllers from multiple files.",
                          metavar="FILE")

        parser.add_option("-I", "--instruments-dir", action="append", dest="inst_dir",
                          help="Append PATH to instruments load path.",
                          metavar="PATH")

        parser.add_option("-C", "--controllers-dir", action="append", dest="ctrl_dir",
                          help="Append PATH to controllers load path.",
                          metavar="PATH")

        parser.add_option("-D", "--drivers-dir", action="append", dest="drv_dir",
                          help="Append PATH to drivers load path.",
                          metavar="PATH")

        parser.add_option("-v", "--verbose", action="store_true", dest='verbose',
                          help="Increase screen log level.")

        parser.set_defaults(instruments = [],
                        controllers = [],
                        drivers     = [],
                        config = [],
                        inst_dir = [],
                        ctrl_dir = [],
                        drv_dir = [],
                        verbose=False)

        return parser.parse_args(args)

    def _setupSignals (self):

        signal.signal(signal.SIGTERM, self._sighandler)
        signal.signal(signal.SIGINT, self._sighandler)

    def _sighandler(self, sig, frame):
        self._shutdown()

    def init(self):

        # setup signal handlers
        self._setupSignals()

        # manager
        self.manager = Manager()

        # config file
        self.config = SiteConfig()
        
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
            l = Location(drv)
            self.manager.initDriver(l)

        for inst in self.config.getInstruments():
            l = Location(inst)
            self.manager.initInstrument(l)

        for ctrl in self.config.getControllers():
            l = Location(ctrl)
            self.manager.initController(l)
            
        # init from cmd line
        for drv in self.options.drivers:
            l = Location(drv)
            self.manager.initDriver(l)

        for inst in self.options.instruments:
            l = Location(inst)
            self.manager.initInstrument(l)

        for ctrl in self.options.controllers:
            l = Location(ctrl)
            self.manager.initController(l)

        # FIXME: this works!?
        # HACK: wow, what a uptime!
        time.sleep (sys.maxint)

    def shutdown (self):
        os.kill (self.pid, signal.SIGTERM)
        
    def _shutdown(self):

        # ok, exit!
        logging.debug("Shutting down system.")
        self.manager.shutdown()
        sys.exit (0)
