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

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.controllers.autofocus import Autofocus, Target, Mode

from chimera.instruments.camera import Camera
from chimera.drivers.fakecamera import FakeCamera
from chimera.drivers.sbig       import SBIG

from chimera.instruments.telescope import Telescope
from chimera.drivers.faketelescope import FakeTelescope
from chimera.drivers.meade         import Meade

from chimera.instruments.dome    import Dome
from chimera.drivers.fakedome    import FakeDome
from chimera.drivers.domelna40cm import DomeLNA40cm

from chimera.util.coord import Coord
from chimera.util.position import Position

import chimera.core.log

import pyfits
import ephem

import time
import sys
import logging
import datetime as dt

chimera.core.log.setConsoleLevel(logging.DEBUG)


class TestAutoMap (object):

    def setup (self):

        self.manager = Manager(port=8000)

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})
        

        # fake
        self.manager.addClass(FakeTelescope, "fake", {"skip_init": False})
        self.manager.addClass(Telescope, "fake", {"driver": "/FakeTelescope/0"})
        
        self.manager.addClass(FakeCamera, "fake")
        self.manager.addClass(Camera, "cam", {"driver": "/FakeCamera/0"})

        self.manager.addClass(FakeDome, "fake")
        self.manager.addClass(Dome, "dome", {"driver": "/FakeDome/0",
                                             "mode": "Track",
                                             "telescope": "/Telescope/0"})

        # real
        #self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6", "skip_init": False})
        #self.manager.addClass(Telescope, "meade", {"driver": "/Meade/meade"})
        
        #self.manager.addClass(SBIG, "sbig", {"device": "USB"})
        #self.manager.addClass(Camera, "cam", {"driver": "/SBIG/0"})

        #self.manager.addClass(DomeLNA40cm, "lna40", {"device": "/dev/ttyS0"})
        #self.manager.addClass(Dome, "dome", {"driver": "/DomeLNA40cm/0",
        #                                     "mode": "Track",
        #                                     "telescope": "/Telescope/0"})
        


        @callback(self.manager)
        def exposeBeginClbk(exp_time):
            print time.time(), "[cam] Expose begin for %.3f s." % exp_time

        @callback(self.manager)
        def exposeCompleteClbk():
            print time.time(), "[cam] Expose complete."

        @callback(self.manager)
        def readoutBeginClbk(frame):
            print time.time(), "[cam] Readout begin for %s." % frame

        @callback(self.manager)
        def readoutCompleteClbk(frame):
            print time.time(), "[cam] Readout complete for %s." % frame

        @callback(self.manager)
        def camAbortCompleteClbk():
            print time.time(), "[cam] Abort complete."

        cam = self.manager.getProxy(Camera)
        cam.exposeBegin     += exposeBeginClbk
        cam.exposeComplete  += exposeCompleteClbk        
        cam.readoutBegin    += readoutBeginClbk        
        cam.readoutComplete += readoutCompleteClbk
        cam.abortComplete   += camAbortCompleteClbk

        @callback(self.manager)
        def slewBeginClbk(target):
            print time.time(), "[tel] Slew begin. target=%s" % str(target)

        @callback(self.manager)
        def slewCompleteClbk(position):
            print time.time(), "[tel] Slew complete. position=%s" % str(position)

        @callback(self.manager)
        def telAbortCompleteClbk(position):
            print time.time(), "[tel] Abort complete. position=%s" % str(position)

        self.tel = self.manager.getProxy(Telescope)
        self.tel.slewBegin      += slewBeginClbk
        self.tel.slewComplete   += slewCompleteClbk
        self.tel.abortComplete  += telAbortCompleteClbk

        @callback(self.manager)
        def domeSlewBeginClbk(target):
            print
            print time.time(), "[dome] Slew begin. target=%s" % str(target)

        @callback(self.manager)
        def domeSlewCompleteClbk(position):
            print time.time(), "[dome] Slew complete. position=%s" % str(position)

        @callback(self.manager)
        def domeAbortCompleteClbk(position):
            print time.time(), "[dome] Abort slew at position=%s" % str(position)

        dome = self.manager.getProxy(Dome)
        dome.slewBegin    += domeSlewBeginClbk
        dome.slewComplete += domeSlewCompleteClbk
        dome.abortComplete+= domeAbortCompleteClbk
        

    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_map (self):

        tel = self.manager.getProxy(Telescope)
        cam = self.manager.getProxy(Camera)
        dome= self.manager.getProxy(Dome)

        site = self.manager.getProxy(Site)

        #tel.slewToRaDec(Position.fromRaDec(10,10))
        #dome.sync()
        #cam.expose(exp_time=10, frames=1, filename="teste")

