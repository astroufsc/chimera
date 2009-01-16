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

from chimera.core.manager    import Manager
from chimera.core.site       import Site
from chimera.core.exceptions import printException

import chimera.core.log

from chimera.util.coord    import Coord
from chimera.util.position import Position

from dateutil.relativedelta import relativedelta

import time
import sys
import logging



class TestSite (object):

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

    def teardown (self):
        self.manager.shutdown()

    def test_times (self):

        site = self.manager.getProxy(Site)

        try:
            print
            print "local:", site.localtime()
            print "UT   :", site.ut()
            print "JD   :", site.JD()
            print "MJD  :", site.MJD()
            print "LST  :", site.LST()
            print "GST  :", site.GST()
        except Exception, e:
            printException(e)


    def test_sidereal_clock (self):

        return True
        
        site = self.manager.getProxy(Site)

        times = []
        real_times = []

        for i in range (100):
            t0 = time.clock()
            t0_r = time.time()
            print "\r%s" % site.LST(),
            times.append(time.clock()-t0)
            real_times.append(time.time()-t0_r)

        print
        print sum(times) / len(times)
        print sum(real_times) / len(real_times)

    def test_astros (self):

        site = self.manager.getProxy(Site)

        try:
            print
            print "local   :", site.localtime()
            print
            print "moonrise  :", site.moonrise()
            print "moonset   :", site.moonset()
            print "moon pos  :", site.moonpos()
            print "moon phase:", site.moonphase()
            print
            print "sunrise:", site.sunrise()
            print "sunset :", site.sunset()
            print "sun pos:", site.sunpos()
            print

            sunset_twilight_begin = site.sunset_twilight_begin()
            sunset_twilight_end   = site.sunset_twilight_end()
            sunset_twilight_duration = relativedelta(sunset_twilight_end, sunset_twilight_begin)
            
            sunrise_twilight_begin = site.sunrise_twilight_begin()
            sunrise_twilight_end = site.sunrise_twilight_end()
            sunrise_twilight_duration = relativedelta(sunrise_twilight_end, sunrise_twilight_begin)            
            
            print "next sunset twilight begins at:", sunset_twilight_begin
            print "next sunset twilight ends   at:", sunset_twilight_end
            print "sunset twilight duration      :", sunset_twilight_duration
            print
            print "next sunrise twilight begins at:", sunrise_twilight_begin
            print "next sunrise twilight ends   at:", sunrise_twilight_end
            print "sunrise twilight duration      :", sunrise_twilight_duration            

        except Exception, e:
            printException(e)
        
