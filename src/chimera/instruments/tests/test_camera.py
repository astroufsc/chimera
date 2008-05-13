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

from chimera.instruments.camera import Camera
from chimera.drivers.fakecamera import FakeCamera

from chimera.drivers.sbig import SBIG

from chimera.interfaces.cameradriver import Device

import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.INFO)
log = logging.getLogger("chimera.tests")


from nose.tools import assert_raises


class TestCamera (object):

    def setup (self):

        self.manager = Manager(port=8000)

        self.manager.addClass(SBIG, "sbig", {"device": Device.USB})
        self.manager.addClass(Camera, "cam", {"driver": "/SBIG/sbig"})

        #self.manager.addClass(FakeCamera, "fake", {"device": Device.USB})
        #self.manager.addClass(Camera, "cam", {"driver": "/FakeCamera/fake"})

        @callback(self.manager)
        def exposeBeginClbk(exp_time):
            print time.time(), "Expose begin for %.3f s." % exp_time

        @callback(self.manager)
        def exposeCompleteClbk():
            print time.time(), "Expose complete."

        @callback(self.manager)
        def readoutBeginClbk(frame):
            print time.time(), "Readout begin for %s." % frame

        @callback(self.manager)
        def readoutCompleteClbk(frame):
            print time.time(), "Readout complete for %s." % frame

        @callback(self.manager)
        def abortCompleteClbk():
            print time.time(), "Abort complete."

        cam = self.manager.getProxy(Camera)
        cam.exposeBegin     += exposeBeginClbk
        cam.exposeComplete  += exposeCompleteClbk        
        cam.readoutBegin    += readoutBeginClbk        
        cam.readoutComplete += readoutCompleteClbk
        cam.abortComplete   += abortCompleteClbk
        
    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_simple (self):

        cam = self.manager.getProxy(Camera)

        assert cam.isExposing() == False

    def test_expose (self):

        print
        
        cam = self.manager.getProxy(Camera)

        frames = 0

        try:
            frames = cam.expose(exp_time=1, frames=5, interval=0.5, filename="test_expose.fits")
        except Exception, e:
            log.exception("problems")

        assert len(frames) == 5        


    def test_expose_checkings (self):

        cam = self.manager.getProxy(Camera)

        # exp_time ranges
        assert_raises(ValueError, cam.expose, exp_time=-1)
        assert_raises(ValueError, cam.expose, exp_time=10e100)

        # frame ranges
        assert_raises(ValueError, cam.expose, exp_time=1, frames=0)
        assert_raises(ValueError, cam.expose, exp_time=1, frames=-1)

        # interval ranges
        assert_raises(ValueError, cam.expose, exp_time=0, interval=-1)

    def test_expose_lock (self):

        cam = self.manager.getProxy(Camera)

        begin_times = []
        end_times = []

        print
        
        @callback(self.manager)
        def exposeBeginClbk(exp_time):
            begin_times.append(time.time())

        @callback(self.manager)
        def readoutCompleteClbk(frame):
            end_times.append(time.time())

        cam.exposeBegin     += exposeBeginClbk
        cam.readoutComplete += readoutCompleteClbk        

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(Camera)
            cam.expose(exp_time=2, filename="test_expose_lock.fits")

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
        
    def test_expose_abort (self):

        cam = self.manager.getProxy(Camera)

        print
        
        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(Camera)
            cam.expose(exp_time=10, filename="test_expose_abort.fits")

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

    def test_cooling (self):

        cam = self.manager.getProxy(Camera)

        def eps_equal(a, b, eps):
            return abs(a-b) <= eps

        cam.stopCooling()
        assert cam.isCooling() == False

        print
        for i in range(10):
            print "\rcurrent temp:", cam.getTemperature(),
            sys.stdout.flush()
            time.sleep(0.5)
        print

        cool=10
        cam.startCooling(cool)
        assert cam.isCooling() == True

        while not eps_equal(cam.getTemperature(), cool, 0.25):
            print "\rwaiting to cool to %d oC:" % cool, cam.getTemperature(),
            sys.stdout.flush()
            time.sleep(1)

        cam.stopCooling()
        assert cam.isCooling() == False

        
