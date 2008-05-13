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


import time
import logging
import random

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.instruments.dome  import Dome
from chimera.interfaces.dome   import InvalidDomePositionException, Mode

from chimera.drivers.fakedome     import FakeDome
#from chimera.drivers.domelna40cm  import DomeLNA40cm

#from chimera.drivers.meade        import Meade
from chimera.drivers.faketelescope import FakeTelescope
from chimera.instruments.telescope import Telescope

from chimera.util.position import Position

import chimera.core.log
chimera.core.log.setConsoleLevel(logging.DEBUG)

from nose.tools import assert_raises


class TestDome (object):

    def setup (self):

        self.manager = Manager()

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})
        
        #self.manager.addClass(Meade, "meade", {"device": "/dev/ttyUSB0"})
        #self.manager.addClass(Telescope, "tel", {"driver": "/Meade/meade"})

        #self.manager.addClass(DomeLNA40cm, "lna40", {"device": "/dev/ttyS0"})
        #self.manager.addClass(Dome, "dome", {"driver": "/DomeLNA40cm/0",
        #                                     "telescope": "/Telescope/0"})

        self.manager.addClass(FakeTelescope, "fake")
        self.manager.addClass(Telescope, "tel", {"driver": "/FakeTelescope/0"})

        self.manager.addClass(FakeDome, "fake")
        self.manager.addClass(Dome, "dome", {"driver": "/FakeDome/0",
                                             "telescope": "/Telescope/0"})

        @callback(self.manager)
        def slewBeginClbk(target):
            print
            print time.time(), "[dome] Slew begin. target=%s" % str(target)

        @callback(self.manager)
        def slewCompleteClbk(position):
            print time.time(), "[dome] Slew complete. position=%s" % str(position)

        @callback(self.manager)
        def abortCompleteClbk(position):
            print time.time(), "[dome] Abort slew at position=%s" % str(position)

        @callback(self.manager)
        def slitOpenedClbk(position):
            print
            print time.time(), "[dome] Slit opened with dome at at position=%s" % str(position)

        @callback(self.manager)
        def slitClosedClbk(position):
            print
            print time.time(), "[dome] Slit closed with dome at at position=%s" % str(position)

        dome = self.manager.getProxy(Dome)
        dome.slewBegin    += slewBeginClbk
        dome.slewComplete += slewCompleteClbk
        dome.abortComplete+= abortCompleteClbk
        dome.slitOpened   += slitOpenedClbk
        dome.slitClosed   += slitClosedClbk     

    def test_get_az (self):
        dome = self.manager.getProxy(Dome)
        assert dome.getAz() >= 0

    def test_slew_to_az (self):
        dome = self.manager.getProxy(Dome)

        start = dome.getAz()
        delta = 20
        
        dome.slewToAz(start+delta)
        
        assert dome.getAz() == (start+delta)

    def test_slit (self):
        
        dome = self.manager.getProxy(Dome)

        dome.openSlit()
        assert dome.isSlitOpen() == True

        dome.closeSlit()
        assert dome.isSlitOpen() == False

    def test_track (self):

        dome = self.manager.getProxy(Dome)
        tel  = self.manager.getProxy(Telescope)

        dome.track()
        assert dome.getMode() == Mode.Track

        p = tel.getPositionRaDec()

        time.sleep(30)
        
        tel.slewToRaDec((p.ra-10, p.dec-10))

        time.sleep(30)

        dome.stand()

        time.sleep(30)


        


        


