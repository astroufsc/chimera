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
import sys
import random
import threading
import logging

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.enum import EnumValue

from chimera.interfaces.dome import InvalidDomePositionException, DomeStatus

from nose import SkipTest
from nose.tools import assert_raises

import chimera.core.log
chimera.core.log.setConsoleLevel(1e10)
log = logging.getLogger("chimera.tests")

# hack for event  triggering asserts
FiredEvents = {}


class DomeTest(object):

    DOME = ""
    TELESCOPE = ""
    manager = None

    def assertEvents(self, slewStatus):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters
        
        assert "slewBegin" in FiredEvents
        assert isinstance(FiredEvents["slewBegin"][1], Coord)

        assert "slewComplete" in FiredEvents
        assert FiredEvents["slewComplete"][0] > FiredEvents["slewBegin"][0]
        assert isinstance(FiredEvents["slewComplete"][1], Coord)
        assert isinstance(FiredEvents["slewComplete"][2], EnumValue) and FiredEvents["slewComplete"][2] in DomeStatus
        assert FiredEvents["slewComplete"][2] == slewStatus

    def setupEvents(self):

        @callback(self.manager)
        def slewBeginClbk(position):
            FiredEvents["slewBegin"] = (time.time(), position)

        @callback(self.manager)
        def slewCompleteClbk(position, status):
            FiredEvents["slewComplete"] = (time.time(), position, status)

        dome = self.manager.getProxy(self.DOME)
        dome.slewBegin += slewBeginClbk
        dome.slewComplete += slewCompleteClbk
        
    def test_stress_dome_track (self):
        # just for manual and visual testing
        raise SkipTest()

        dome = self.manager.getProxy(self.DOME)
        tel  = self.manager.getProxy(self.TELESCOPE)

        dome.track()

        for i in range(10):
            ra  = "%d %d 00" % (random.randint(7,15), random.randint(0,59))
            dec = "%d %d 00" % (random.randint(-90,0), random.randint(0,59))
            tel.slewToRaDec(Position.fromRaDec(ra, dec))
            dome.syncWithTel()

            time.sleep(random.randint(0,10))

    def test_stress_dome_slew (self):

        # just for manual and visual testing
        raise SkipTest()

        dome = self.manager.getProxy(self.DOME)

        print

        quit = threading.Event()

        def get_az_stress ():
            while not quit.isSet():
                dome.getAz()
                time.sleep(0.5)

        az_thread = threading.Thread(target=get_az_stress)
        az_thread.start()

        for i in range(10):
            az = random.randint(0,359)
            dome.slewToAz(Coord.fromD(az))
            time.sleep(5)

        quit.set()
        az_thread.join()


    def test_get_az (self):
        dome = self.manager.getProxy(self.DOME)
        assert dome.getAz() >= 0

    def test_slew_to_az (self):

        dome = self.manager.getProxy(self.DOME)

        start = dome.getAz()
        delta = 20
        
        dome.slewToAz(start+delta)
        
        assert dome.getAz() == (start+delta)

        assert_raises(InvalidDomePositionException, dome.slewToAz, 9999)

        # event check
        self.assertEvents(DomeStatus.OK)

    def test_slit (self):
        
        dome = self.manager.getProxy(self.DOME)

        dome.openSlit()
        assert dome.isSlitOpen() == True

        dome.closeSlit()
        assert dome.isSlitOpen() == False



#
# setup real and fake tests
#

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

class TestFakeDome(FakeHardwareTest, DomeTest):

    def setup (self):

        self.manager = Manager()

        self.manager.addClass(Site, "lna", {"name": "UFSC",
                                            "latitude": "-27 36 13 ",
                                            "longitude": "-48 31 20",
                                            "altitude": "20",
                                            "utc_offset": "-3"})

        from chimera.instruments.faketelescope import FakeTelescope
        from chimera.instruments.fakedome import FakeDome
        self.manager.addClass(FakeTelescope, "fake")
        self.manager.addClass(FakeDome, "dome", {"telescope": "/FakeTelescope/0",
                                                 "mode": "Track"})
        self.TELESCOPE = "/FakeTelescope/0"
        self.DOME = "/FakeDome/0"

        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()


class TestRealDome(RealHardwareTest, DomeTest):
    
    def setup (self):

        self.manager = Manager()

        self.manager.addClass(Site, "lna", {"name": "UFSC",
                                            "latitude": "-27 36 13 ",
                                            "longitude": "-48 31 20",
                                            "altitude": "20",
                                            "utc_offset": "-3"})

        from chimera.instruments.domelna40cm import DomeLNA40cm
        from chimera.instruments.meade       import Meade
        self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        self.manager.addClass(DomeLNA40cm, "lna40", {"device": "/dev/ttyS9",
                                                     "telescope": "/Meade/0",
                                                     "mode": "Stand"})

        self.TELESCOPE = "/Meade/meade"
        self.DOME = "/DomeLNA40cm/0"
       
        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()
