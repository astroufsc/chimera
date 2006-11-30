#! /usr/bin/python
#! -*- coding: iso-8859-1 -*-

from uts.core.register import Register
from uts.core.config import SiteConfiguration
from uts.core.threads import ThreadPool
from uts.core.proxy import Proxy
from uts.core.location import Location
from uts.core.manager import Manager

from uts.core.version import _uts_version

import signal
import os
import os.path
import distutils.sysconfig
import logging
import threading

from optparse import OptionParser

# FIXME: handle instruments and controllers main function error

class Site(object):

    def __init__(self, args = []):

        self.options, self.args = self.parseArgs(args)

        # verbosity level
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(module)s:%(lineno)d %(message)s',
                            datefmt='%d-%m-%Y %H:%M:%S (%j)')

        if self.options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        logging.debug("Starting system.")

        # manager
        self.manager = Manager()

        # directories

        for _dir in self.options.inst_dir:
            self.manager.appendPath("instrument", _dir)

        for _dir in self.options.ctrl_dir:
            self.manager.appendPath("controller", _dir)

        for _dir in self.options.drv_dir:
            self.manager.appendPath("driver", _dir)


    def parseArgs(self, args):

        parser = OptionParser(prog="UTS", version=_uts_version,
                              description="UTS - Unified Telescope System")

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

	prefix = os.path.realpath(os.path.join(os.path.abspath(__file__), '../../'))
        
	parser.set_defaults(instruments = [],
                        controllers = [],
                        drivers     = [],
                        config = [],
                        inst_dir = [os.path.join(prefix, 'instruments')],
                        ctrl_dir = [os.path.join(prefix, 'controllers')],
                        drv_dir = [os.path.join(prefix, 'drivers')],
                        verbose=False)

        return parser.parse_args(args)

    def init(self):
        self._pool = ThreadPool(10)
        self.manager.setPool(self._pool)

        # config file
        self.config = SiteConfiguration()
        
        for config in self.options.config:
            self.config.read(config)

        for drv in self.config.getDrivers():
            l = Location(drv)
            self.manager.initDriver(l)

        for inst in self.config.getInstruments():
            l = Location(inst)
            self.manager.initInstrument(l)

        for ctrl in self.config.getControllers():
            l = Location(ctrl)
            self.manager.initController(l)
            
        # add all instruments from config and from cmdline
        for drv in self.options.drivers:
            l = Location(drv)
            self.manager.initDriver(l)

        for inst in self.options.instruments:
            l = Location(inst)
            self.manager.initInstrument(l)

        for ctrl in self.options.controllers:
            l = Location(ctrl)
            self.manager.initController(l)

    def shutdown(self):
        self.manager.shutdown()
        logging.debug("Shutting down system.")

def main(args):

    def splitAndWatch(shutdown, finish):

        child = os.fork()

        if child == 0:
            return

        def kill():
            shutdown()
            finish.set()
            os.kill(child, signal.SIGKILL)

        def sighandler(sig, frame):
            kill()

        signal.signal(signal.SIGTERM, sighandler)
        signal.signal(signal.SIGINT, sighandler)

        try:
            os.wait()
            shutdown()
            finish.set()
            
        except OSError:
            pass

    # ============

    # FIXME Ugly hacks to python threading works with signal
    # FIXME see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
    # FIXME see http://greenteapress.com/semaphores/

    mainProcess = threading.Event()

    # only initialize, DON'T run threads here!

    s = Site(args)

    # from here we have 2 process. Child will return from splitAndWatch,
    # while the main process will watch for signals and will kill the child
    # process and set mainProcess event so the remaining of the code
    # know what execute
    
    splitAndWatch(s.shutdown, mainProcess)

    # child run the thread
    if not mainProcess.isSet():
        s.init()
    else:
        # run whatever you want on the main thread
        pass

if __name__ == '__main__':

    import sys

    main(sys.argv)

