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

        @callback(self.manager)
        def slewBeginClbk(target):
            print time.time(), "Slew begin. target=%s" % str(target)

        @callback(self.manager)
        def slewCompleteClbk(position):
            print time.time(), "Slew complete. position=%s" % str(position)

        @callback(self.manager)
        def abortCompleteClbk(position):
            print time.time(), "Abort complete. position=%s" % str(position)

        @callback(self.manager)
        def syncCompleteClbk(position):
            print time.time(), "Sync complete. position=%s" % str(position)

        @callback(self.manager)
        def parkCompleteClbk():
            print time.time(), "Park complete..."

        @callback(self.manager)
        def unparkCompleteClbk():
            print time.time(), "Unpark complete..."

        self.tel = self.manager.getProxy(Telescope)
        self.tel.slewBegin      += slewBeginClbk
        self.tel.slewComplete   += slewCompleteClbk
        self.tel.abortComplete  += abortCompleteClbk
        self.tel.syncComplete   += syncCompleteClbk
        self.tel.parkComplete   += parkCompleteClbk
        self.tel.unparkComplete += unparkCompleteClbk

    def test_slew (self):

        ra  = self.tel.getRa()
        dec = self.tel.getDec()

        print
        print "current position:", self.tel.getPositionRaDec()
        print "moving to:", (ra-"1 00 00"), (dec-"15 00 00")

        self.tel.slewToRaDec((ra-"1 00 00", dec-"15 00 00"))

        print "new position:", self.tel.getPositionRaDec()

    def test_slew_abort (self):

        p =  self.tel.getPositionRaDec()

        print
        print "current position:", p
        print "moving to:", (p.ra-"10 00 00"), (p.dec-"10 00 00")

        def slew():
            tel = self.manager.getProxy(Telescope)
            tel.slewToRaDec((p.ra-"10 00 00", p.dec-"10 00 00"))

        pool = ThreadPool()
        pool.queueTask(slew)

        time.sleep(2)

        self.tel.abortSlew()

        print "new position:", self.tel.getPositionRaDec()

    def test_sync (self):

        start = self.tel.getPositionRaDec()

        ra  = self.tel.getRa()
        dec = self.tel.getDec()

        print

        print "current position:", self.tel.getPositionRaDec()
        print "moving to:", (ra-"01 00 00"), (dec-"01 00 00")

        self.tel.slewToRaDec((ra-"01 00 00", dec-"01 00 00"))

        print "syncing on:", start

        self.tel.syncRaDec(start)

        print "current position:", self.tel.getPositionRaDec()

    def test_park (self):

        def printPosition():
            print self.tel.getPositionRaDec(), self.tel.getPositionAzAlt()
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
        wait = 120

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

        
        
    

        
