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

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.interfaces.dome   import InvalidDomePositionException

from nose.tools import assert_raises


class TestDome (object):

    DOME = ""
    TELESCOPE = ""

    def setup (self):

        self.manager = Manager()

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})

        if "REAL" in sys.argv:
            from chimera.instruments.domelna40cm import DomeLNA40cm
            from chimera.instruments.meade       import Meade

            self.manager.addClass(Meade, "meade", {"device": "/dev/ttyUSB0"})
            self.manager.addClass(DomeLNA40cm, "lna40", {"device": "/dev/ttyS0",
                                                         "telescope": "/Meade/0"})
            self.DOME = "/DomeLNA40cm/0"
            self.TELESCOPE = "/Meade/0"
        else:
            from chimera.instruments.fakedome      import FakeDome
            from chimera.instruments.faketelescope import FakeTelescope

            self.manager.addClass(FakeTelescope, "fake")
            self.manager.addClass(FakeDome, "fake", {"telescope": "/FakeTelescope/0"})
            self.DOME = "/FakeDome/0"
            self.TELESCOPE = "/FakeTelescope/0"

        @callback(self.manager)
        def slewBeginClbk(target):
            print
            print time.time(), "[dome] Slew begin. target=%s" % str(target)
            print

        @callback(self.manager)
        def slewCompleteClbk(position):
            print
            print time.time(), "[dome] Slew complete. position=%s" % str(position)
            print

        @callback(self.manager)
        def abortCompleteClbk(position):
            print
            print time.time(), "[dome] Abort slew at position=%s" % str(position)
            print

        @callback(self.manager)
        def slitOpenedClbk(position):
            print
            print time.time(), "[dome] Slit opened with dome at at position=%s" % str(position)
            print

        @callback(self.manager)
        def slitClosedClbk(position):
            print
            print time.time(), "[dome] Slit closed with dome at at position=%s" % str(position)
            print

        dome = self.manager.getProxy(self.DOME)
        dome.slewBegin    += slewBeginClbk
        dome.slewComplete += slewCompleteClbk
        dome.abortComplete+= abortCompleteClbk
        dome.slitOpened   += slitOpenedClbk
        dome.slitClosed   += slitClosedClbk     

    def teardown (self):
        self.manager.shutdown()

    def test_stress_dome_track (self):
        dome = self.manager.getProxy(self.DOME)
        tel  = self.manager.getProxy(self.TELESCOPE)

        dome.track()

        for i in range(25):
            ra  = "%d %d 00" % (random.randint(0,23), random.randint(0,59))
            dec = "%d %d 00" % (random.randint(-90,0), random.randint(0,59))
            tel.slewToRaDec((ra, dec))
            time.sleep(random.randint(0,10))

        dome.syncWithTel()

    def test_stress_dome_slew (self):

        dome = self.manager.getProxy(self.DOME)

        for i in range(25):
            az = random.randint(0,359)
            dome.slewToAz(az)
            assert dome.getAz() == az

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

    def test_slit (self):
        
        dome = self.manager.getProxy(self.DOME)

        dome.openSlit()
        assert dome.isSlitOpen() == True

        dome.closeSlit()
        assert dome.isSlitOpen() == False



        


