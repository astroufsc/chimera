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
import sys

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.threads  import ThreadPool
from chimera.core.exceptions import ChimeraValueError
from chimera.core.proxy import Proxy

import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.DEBUG)
log = logging.getLogger("chimera.tests")


from nose.tools import assert_raises


class TestCamera (object):

    CAMERA = ""

    def setup (self):

        self.manager = Manager(port=8000)

        if "REAL" in sys.argv:
            from chimera.intruments.sbig import SBIG
            self.manager.addClass(SBIG, "sbig")
            self.CAMERA = "/SBIG/0"
        else:
            from chimera.instruments.fakecamera import FakeCamera
            self.manager.addClass(FakeCamera, "fake")
            self.CAMERA = "/FakeCamera/0"

        @callback(self.manager)
        def exposeBeginClbk(request):
            print
            print time.time(), "Expose begin for request %s." % request

        @callback(self.manager)
        def exposeCompleteClbk(request):
            print time.time(), "Expose complete for request %s." % request

        @callback(self.manager)
        def readoutBeginClbk(request):
            print time.time(), "Readout begin for request %s." % request["filename"]

        @callback(self.manager)
        def readoutCompleteClbk(img):
            print time.time(), "Readout complete for request %s." % img.filename()

        @callback(self.manager)
        def abortCompleteClbk():
            print time.time(), "Abort complete."

        cam = self.manager.getProxy(self.CAMERA)
        cam.exposeBegin     += exposeBeginClbk
        cam.exposeComplete  += exposeCompleteClbk        
        cam.readoutBegin    += readoutBeginClbk        
        cam.readoutComplete += readoutCompleteClbk
        cam.abortComplete   += abortCompleteClbk
        
    def teardown (self):
        self.manager.shutdown()

    def test_simple (self):

        cam = self.manager.getProxy(self.CAMERA)
        assert cam.isExposing() == False

    def test_expose (self):

        cam = self.manager.getProxy(self.CAMERA)

        frames = 0

        try:
            frames = cam.expose(exptime=2, frames=2, interval=0.5, filename="autogen-expose.fits")
        except Exception, e:
            log.exception("problems")

        assert len(frames) == 2  
        assert isinstance(frames[0], Proxy)
        assert isinstance(frames[1], Proxy)

    def test_expose_checkings (self):

        cam = self.manager.getProxy(self.CAMERA)

        # exp_time ranges
        assert_raises(ChimeraValueError, cam.expose, exptime=-1)
        assert_raises(ChimeraValueError, cam.expose, exptime=1e100)

        # frame ranges
        assert_raises(ChimeraValueError, cam.expose, exptime=1, frames=0)
        assert_raises(ChimeraValueError, cam.expose, exptime=1, frames=-1)

        # interval ranges
        assert_raises(ChimeraValueError, cam.expose, exptime=0, interval=-1)

    def test_expose_lock (self):

        cam = self.manager.getProxy(self.CAMERA)

        begin_times = []
        end_times = []

        @callback(self.manager)
        def exposeBeginClbk(request):
            begin_times.append(time.time())

        @callback(self.manager)
        def readoutCompleteClbk(request):
            end_times.append(time.time())

        cam.exposeBegin     += exposeBeginClbk
        cam.readoutComplete += readoutCompleteClbk        

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=2, filename="autogen-expose-lock.fits")

        pool = ThreadPool()
        pool.queueTask(doExpose)
        pool.queueTask(doExpose)

        # wait doExpose to be scheduled
        time.sleep(1)        

        while len(end_times) < 2: time.sleep(1)

        # rationale: first exposure will start and the next will wait,
        # so we can never get the second exposure beginning before exposure one readout finishes.
        assert len(begin_times) == 2
        assert len(end_times) == 2
        assert (end_times[1] > begin_times[0])

        pool.joinAll()
        
    def test_expose_abort (self):

        cam = self.manager.getProxy(self.CAMERA)

        print
        
        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=10, filename="autogen-expose-abort.fits")

        #
        # abort exposure while exposing
        #

        pool = ThreadPool()
        pool.queueTask(doExpose)

        # thread scheduling
        time.sleep(2)

        assert cam.isExposing() == True
        cam.abortExposure()
        assert cam.isExposing() == False

        pool.joinAll()

    def test_cooling (self):

        cam = self.manager.getProxy(self.CAMERA)

        def eps_equal(a, b, eps):
            return abs(a-b) <= eps

        cam.stopCooling()
        assert cam.isCooling() == False

        cool=10
        cam.startCooling(cool)
        assert cam.isCooling() == True

        print
        while not eps_equal(cam.getTemperature(), cool, 0.25):
            print "\rwaiting to cool to %d oC:" % cool, cam.getTemperature(),
            sys.stdout.flush()
            time.sleep(1)

        cam.stopCooling()
        assert cam.isCooling() == False
