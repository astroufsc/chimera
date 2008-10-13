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
import logging

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site
from chimera.core.threads  import ThreadPool

from chimera.instruments.telescope import Telescope
from chimera.drivers.faketelescope import FakeTelescope

from chimera.drivers.meade import Meade

import chimera.core.log

from chimera.util.coord    import Coord
from chimera.util.position import Position


def assertEpsEqual (a, b, e=60):
    """Assert wether a equals b withing eps precision, in
    arcseconds. Both a and b must be Coords.
    """
    assert abs(a.AS-b.AS) <= e

class TestTelescope (object):

    def setup (self):

        self.manager = Manager(port=8000)

        #self.manager.addClass(Site, "lna", {"name": "LNA",
        #                                    "latitude": "-22 32 03",
        #                                    "longitude": "-45 34 57",
        #                                    "altitude": "1896",
        #                                    "utc_offset": "-3"})

        self.manager.addClass(Site, "lna", {"name": "UFSC",
                                            "latitude": "-27 36 13 ",
                                            "longitude": "-48 31 20",
                                            "altitude": "20",
                                            "utc_offset": "-3"})

        #self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        #self.manager.addClass(Telescope, "meade", {"driver": "/Meade/meade"})

        self.manager.addClass(FakeTelescope, "fake")
        self.manager.addClass(Telescope, "fake", {"driver": "/FakeTelescope/fake"})

        #self.manager.addClass(Telescope, "meade",
        #                      {"driver": "200.131.64.134:7666/TheSkyTelescope/0"})

        self.tel = self.manager.getProxy(Telescope)

    def teardown (self):
        self.manager.shutdown()

    def test_slew (self):

        ra  = self.tel.getRa()
        dec = self.tel.getDec()

        dest_ra  = (ra+"1 00 00")
        dest_dec = (dec+"15 00 00")

        @callback(self.manager)
        def slewBeginClbk(target):
            assert target.ra == dest_ra
            assert target.dec == dest_dec

        @callback(self.manager)
        def slewCompleteClbk(position):
            assertEpsEqual(position.ra, dest_ra, 60)
            assertEpsEqual(position.dec, dest_dec, 60)

        self.tel.slewBegin += slewBeginClbk
        self.tel.slewComplete += slewCompleteClbk

        self.tel.slewToRaDec((dest_ra, dest_dec))

    def test_slew_abort (self):

        last_ra  = self.tel.getRa()
        last_dec = self.tel.getDec()

        dest_ra  = last_ra  + "01 00 00"
        dest_dec = last_dec + "10 00 00"

        @callback(self.manager)
        def abortCompleteClbk(position):
            assert last_ra  < position.ra  < dest_ra
            assert last_dec < position.dec < dest_dec

        self.tel.abortComplete += abortCompleteClbk

        # async slew
        def slew():
            self.tel = self.manager.getProxy(Telescope)
            self.tel.slewToRaDec((dest_ra, dest_dec))

        pool = ThreadPool()
        pool.queueTask(slew)

        # wait thread to be scheduled
        time.sleep(2)

        # abort and test (on abortCompleteClbk).
        self.tel.abortSlew()

        pool.joinAll()

    def test_sync (self):

        # get current position, drift the scope, and sync on the first
        # position (like done when aligning the telescope).

        real_ra  = self.tel.getRa()
        real_dec = self.tel.getDec()

        @callback(self.manager)
        def syncCompleteClbk(position):
            assert position.ra == real_ra
            assert position.dec == real_dec

        self.tel.syncComplete += syncCompleteClbk

        # drift to "real" object coordinate
        self.tel.slewToRaDec((real_ra+"01 00 00", real_dec+"01 00 00"))

        self.tel.syncRaDec((real_ra, real_dec))

    def test_park (self):
        
        # FIXME: make a real test.
        return

        def printPosition():
            print self.tel.getPositionRaDec(), self.tel.getPositionAltAz()
            sys.stdout.flush()
            
        print

        ra  = self.tel.getRa()
        dec = self.tel.getDec()

        print "current position:", self.tel.getPositionRaDec()
        print "moving to:", (ra-"01 00 00"), (dec-"01 00 00")

        self.tel.slewToRaDec((ra-"01 00 00", dec-"01 00 00"))

        for i in range(10):
            printPosition()
            time.sleep(0.5)

        print "parking..."
        sys.stdout.flush()
        self.tel.park()

        t0 = time.time()
        wait = 30

        for i in range(10):
            printPosition()
            time.sleep(0.5)
       
        while time.time() < t0+wait:
            print "\rwaiting ... ",
            sys.stdout.flush()
            time.sleep(1)

        print "unparking..."
        sys.stdout.flush()

        self.tel.unpark()

        for i in range(10):
            printPosition()
            time.sleep(0.5)

        
        
    

        
