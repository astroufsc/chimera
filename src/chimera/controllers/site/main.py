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


import os.path
import logging
import optparse
import sys
import platform

from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.systemconfig import SystemConfig
from chimera.core.version import _chimera_version_, _chimera_description_, find_dev_version
from chimera.core.exceptions import printException, InvalidLocationException, ChimeraException
from chimera.core.constants import (MANAGER_DEFAULT_HOST,
                                    MANAGER_DEFAULT_PORT,
                                    SYSTEM_CONFIG_DEFAULT_FILENAME,
                                    SYSTEM_CONFIG_DEFAULT_GLOBAL)

from chimera.core.site import Site
from chimera.core.path import ChimeraPath

import chimera.core.log


log = logging.getLogger(__name__)


class SiteController (object):

    def __init__(self, args = [], wait=True):
        
        self.wait = wait

        self.options, self.args = self.parseArgs(args)

        if self.options.verbose == 1:
            chimera.core.log.setConsoleLevel(logging.INFO)
            
        if self.options.verbose > 1:
            chimera.core.log.setConsoleLevel(logging.DEBUG)

        self.manager = None

        self.paths = {"instruments": [],
                      "controllers": []}

        # add system path
        self.paths["instruments"].append(ChimeraPath.instruments())
        self.paths["controllers"].append(ChimeraPath.controllers())

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

        parser = optparse.OptionParser(prog="chimera", version=find_dev_version() or _chimera_version_,
                                       description=_chimera_description_,
                                       usage="chimera --help for more information")

        manag_group = optparse.OptionGroup(parser, "Basic options")
        manag_group.add_option("-H", "--host", action="store", 
                               dest="pyro_host", type="string",
                               help="Host name/IP address to run as; [default=%default]",
                               metavar="HOST")

        manag_group.add_option("-P", "--port", action="store", 
                               dest="pyro_port", type="string",
                               help="Port on which to listen for requests; [default=%default]",
                               metavar="PORT")

        config_group = optparse.OptionGroup(parser, "Configuration")

        config_group.add_option("--config", dest="config_file",
                              help="Start Chimera using configuration from FILE.", metavar="FILE")

        config_group.add_option("--skip-global", action="store_false", 
                              dest="use_global",
                              help="Don't use global coniguration file.")

        config_group.add_option("--daemon", action="store_true", dest='daemon',
                              help="Run Chimera in Daemon mode (will detach from current terminal).")

        misc_group = optparse.OptionGroup(parser, "General")

        misc_group.add_option("--dry-run", action="store_true", 
                              dest="dry",
                              help="Only list all configured objects (from command line and configuration files) without starting the system.")
        
        misc_group.add_option("-v", "--verbose", action="count", dest='verbose',
                              help="Increase log level (multiple v's to increase even more).")

        inst_group = optparse.OptionGroup(parser, "Instruments and Controllers Management")

        inst_group.add_option("-i", "--instrument", action="callback", callback=check_location,
                              dest="instruments", type="string",
                              help="Load the instrument defined by LOCATION."
                              "This option could be setted many times to load multiple instruments.",
                              metavar="LOCATION")

        inst_group.add_option("-c", "--controller", action="callback", callback=check_location,
                              dest="controllers", type="string",
                              help="Load the controller defined by LOCATION."
                              "This option could be setted many times to load multiple controllers.",
                              metavar="LOCATION")

        inst_group.add_option("-I", "--instruments-dir", action="callback", callback=check_includepath,
                              dest="inst_dir", type="string",
                              help="Append PATH to instruments load path.",
                              metavar="PATH")

        inst_group.add_option("-C", "--controllers-dir", action="callback", callback=check_includepath,
                              dest="ctrl_dir", type="string",
                              help="Append PATH to controllers load path.",
                              metavar="PATH")

        parser.add_option_group(manag_group)
        parser.add_option_group(config_group)        
        parser.add_option_group(misc_group)
        parser.add_option_group(inst_group)

        parser.set_defaults(instruments = [],
                            controllers = [],
                            config_file = SYSTEM_CONFIG_DEFAULT_FILENAME,
                            inst_dir = [],
                            ctrl_dir = [],
                            drv_dir = [],
                            dry=False,
                            use_global=True,
                            verbose = 0,
                            daemon=False,
                            pyro_host=MANAGER_DEFAULT_HOST,
                            pyro_port=MANAGER_DEFAULT_PORT)

        return parser.parse_args(args)

    def startup(self):

        if self.options.daemon:
            # detach
            log.info("FIXME: Daemon...")
            
        # system config
        try:
            self.config = SystemConfig.fromFile(self.options.config_file, self.options.use_global)
        except (InvalidLocationException, IOError), e:
            log.exception(e)
            log.error("There was a problem reading your configuration file. (%s)" % e)
            sys.exit(1)
        
        # manager
        if not self.options.dry:
            log.info("Starting system.")
            log.info("Chimera: %s" % find_dev_version() or _chimera_version_)
            log.info("Chimera prefix: %s" % ChimeraPath.root())
            log.info("Python: %s" % platform.release())
            log.info("System: %s" % ' '.join(platform.uname()))
                
            try:
                self.manager = Manager(**self.config.chimera)
            except ChimeraException, e:
                log.error("Chimera is already running on this machine. Use chimera-admin to manage it.")
                sys.exit(1)

            log.info("Chimera: running on "+ self.manager.getHostname() + ":" + str(self.manager.getPort()))
            if self.options.use_global:
                log.info("Chimera: reading configuration from %s" % SYSTEM_CONFIG_DEFAULT_GLOBAL)            
            log.info("Chimera: reading configuration from %s" % os.path.realpath(self.options.config_file))

        # add site object
        if not self.options.dry:
            
            for site in self.config.sites:
                self.manager.addClass(Site, site.name, site.config, True)
            
        # search paths
        log.info("Setting objects include path from command line parameters...")
        for _dir in self.options.inst_dir:
            self.paths["instruments"].append(_dir)
    
        for _dir in self.options.ctrl_dir:
            self.paths["controllers"].append(_dir)
        
        # init from config
        log.info("Trying to start instruments...")
        for inst in self.config.instruments + self.options.instruments:
            
            if self.options.dry:
                print inst
            else:
                self._add(inst, path=self.paths["instruments"], start=True)

        log.info("Trying to start controllers...")                
        for ctrl in self.config.controllers + self.options.controllers:
            
            if self.options.dry:
                print ctrl
            else:
                self._add(ctrl, path=self.paths["controllers"], start=True)

        log.info("System up and running.")

        # ok, let's wait manager work
        if self.wait and not self.options.dry:
            self.manager.wait()

    def _add (self, location, path, start):
        try:
            self.manager.addLocation(location, path, start)
        except Exception, e:
            printException(e)
            
    def shutdown(self):
        log.info("Shutting down system.")
        self.manager.shutdown()

