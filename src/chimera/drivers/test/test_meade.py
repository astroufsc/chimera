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
import datetime as dt
import sys

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.interfaces.telescopedriver import SlewRate, AlignMode

from chimera.drivers.meade import Meade

import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.DEBUG)

log = logging.getLogger("chimera.test_meade")

from chimera.util.coord    import Coord
from chimera.util.position import Position

from chimera.util.output import update_scroll_spinner

class TestMeade (object):

    def setup (self):

        self.manager = Manager(port=8000)

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})

        self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS0"})

        @callback(self.manager)
        def slewBeginClbk(target):
            print time.time(), "Slew begin. target=%s" % str(target)

        @callback(self.manager)
        def slewCompleteClbk(position):
            print time.time(), "Slew complete. position=%s" % str(position)

        @callback(self.manager)
        def parkCompleteClbk(position):
            print time.time(), "Park complete. position=%s" % str(position)

        @callback(self.manager)
        def unparkCompleteClbk(position):
            print time.time(), "Unpark complete. position=%s" % str(position)

        self.m = self.manager.getProxy(Meade)
        self.m.slewBegin    += slewBeginClbk
        self.m.slewComplete += slewCompleteClbk
        self.m.parkComplete += parkCompleteClbk
        self.m.unparkComplete += unparkCompleteClbk


    def test_print_info (self):

        m = self.m

        print "align mode:", m.getAlignMode()
        print "ra :", m.getRa()
        print "dec:", m.getDec()
        print "az :", m.getAz()
        print "alt:", m.getAlt()
        
        print "lat :", m.getLat()
        print "long:", m.getLong()
        
        print "date:" , m.getDate()
        print "time:" , m.getLocalTime()
        print "to utc:", m.getUTCOffset()
        print "lst:", m.getLocalSiderealTime()

        print "tracking rate:", m.getCurrentTrackingRate ()

    def test_set_info (self):

        m = self.m

        try:
            m.setLat("-22 32 03")
            m.setLong("-45 34 57")
            m.setDate(time.time())
            m.setLocalTime(time.time())
            m.setUTCOffset(3)

            m.setLat(Coord.fromDMS("-22 32 03"))
            m.setLong(Coord.fromDMS("-45 34 57"))
            m.setDate(dt.date.today())
            m.setLocalTime(dt.datetime.now().time())
            m.setUTCOffset(3)
        except Exception:
            log.exception("error")

    def printCoord (self, header=False):

        m = self.m

        if header:
            print "%20s %20s %20s %20s %20s" % ("LST", "RA", "DEC", "AZ", "ALT")

        print "%20s %20s %20s %20s %20s" % (m.getLocalSiderealTime(),
                                            m.getRa(), m.getDec(), m.getAz(), m.getAlt())

    def test_sync (self):
        # FIXME
        m = self.m
        print "syncing..."
        m.sync ("10 00 00", "00 00 00")

    def test_slew_rate (self):
        m = self.m
        print
        print "current slew rate:", m.getSlewRate()
        
        for rate in SlewRate:
            m.setSlewRate(rate)
            print "current slew rate:", m.getSlewRate()

    def test_movement (self):
        m = self.m

        print

        for rate in SlewRate:
                
            print "moving to East at %s rate:" % rate,
            
            t = time.time ()
            m.moveEast (5, rate)
            print time.time () - t
                
            print "moving to West at %s rate:" % rate,

            t = time.time ()
            m.moveWest (5, rate)
            print time.time () - t

            print "moving to North at %s rate:" % rate,
                        
            t = time.time ()
            m.moveNorth (5, rate)
            print time.time () - t

            print "moving to South at %s rate:" % rate,
            
            t = time.time ()
            m.moveSouth (5, rate)
            print time.time () - t

            print
            print

    def test_align_mode (self):

        m = self.m

        for mode in AlignMode:
            print "current align mode:", m.getAlignMode()
            print "switching to:", mode

            m.setAlignMode (mode)

            print "current align mode:", m.getAlignMode()
            print

    def test_tracking (self):

        m = self.m

        print

        m.setAlignMode (AlignMode.POLAR)
        print "current align mode:", m.getAlignMode()

        print "setting new date and time..."
        self.test_set_info()

        print
        self.printCoord(header=True)
        for i in range(10):
            self.printCoord ()
            time.sleep (1)

        print "stopping tracking..."
        sys.stdout.flush()
            
        m.stopTracking()

        start = time.time ()
        finish = start + 30

        print "waiting",
        sys.stdout.flush ()

        while time.time() < finish:
            time.sleep (1)
            
        print "re-starting tracking..."
        sys.stdout.flush()

        m.startTracking()

        print "using old date and time..."
        print
        self.printCoord(header=True)
        for i in range(10):
            self.printCoord ()
            time.sleep (1)

        print
        print "setting new date and time..."
        self.test_set_info()
        
        print
        for i in range(10):
            self.printCoord ()
            time.sleep (1)

    def test_park (self):

        m = self.m

        print
        print "="*50
        print "Park and unpark test"
        print "="*50
        
        print "Initial conditions (post power-on):"
        self.test_print_info()
        print

        print "Starting the scope..."
        self.test_set_info()
        print

        print "Scope location, date, time updated, new conditions:"
        self.test_print_info()
        print


        print "Pooling telescope position:"

        ra = m.getRa()

        self.printCoord(header=True)
        for i in range(10):
            self.printCoord ()
            time.sleep (1)

        print

        print "Slewing... to %s -70:00:00" % ra
        m.slewToRaDec (Position.fromRaDec(ra, "-70:00:00"))
        print
            
        print "Parking the scope at %s (lst: %s)" % (time.strftime("%c"), m.getLocalSiderealTime())

        m.park ()

        print

        print "Pooling telescope position:"

        self.printCoord(header=True)
        for i in range(10):
            self.printCoord ()
            time.sleep (1)

        print

        start = time.time ()
        finish = start + (2*60) # wait 30 minutes

        print "Waiting              ",
        
        while time.time() < finish:
            update_scroll_spinner()
            time.sleep (0.2)
            
        print

        print "Unparking the scope at %s (lst: %s)" % (time.strftime("%c"),
                                                       m.getLocalSiderealTime())

        m.unpark ()
        print

        print "Pooling telescope position:"

        for i in range(10):
            self.printCoord ()
            time.sleep (1)
            
        print "="*50

    def test_slew_to_az_alt (self):

        # FIXME

        m = self.m

        self.printCoord()

        m.slewToAzAlt(("180:00:00", "40:00:00"))

        self.printCoord()

    def test_slew_to_ra_dec (self):

        m = self.m

        print
        self.printCoord (header=True)

        ra = m.getRa()

        m.slewToRaDec (Position.fromRaDec(ra, "-70:00:00"))
        #m.slewToRaDec (Position.fromRaDec("13h25m38.903s", "-11:12:24.928"))

        self.printCoord()

    def test_move_calibration (self):
        
        print "Calibrating movement..."
        self.m.calibrateMove()

        for rate in SlewRate:
            start = self.m.getPositionRaDec()
            print rate, start, "moving 30\" E..."
            self.m.moveEast(30, rate)
            end = self.m.getPositionRaDec()
            print rate, end, "real =", end.angsep(start).arcsec()
            

            start = self.m.getPositionRaDec()
            print rate, start, "moving 30\" W..."
            self.m.moveWest(30, rate)
            end = self.m.getPositionRaDec()
            print rate, end, "real =", end.angsep(start).arcsec()
            

            start = self.m.getPositionRaDec()
            print rate, start, "moving 30\" N..."
            self.m.moveNorth(30, rate)
            end = self.m.getPositionRaDec()
            print rate, end, "real =", end.angsep(start).arcsec()
            

            start = self.m.getPositionRaDec()
            print rate, start, "moving 30\" S..."
            self.m.moveSouth(30, rate)
            end = self.m.getPositionRaDec()
            print rate, end, "real =", end.angsep(start).arcsec()

            print
            
        
    
