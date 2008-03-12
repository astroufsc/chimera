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

from chimera.core.manager  import Manager
from chimera.core.callback import callback

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

    def test_simplest (self):

        cam = self.manager.getProxy(Camera)

        assert cam.isExposing() == False

    def test_normal_expose (self):

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
        
        self.manager.getPool().queueTask(doExpose)
        self.manager.getPool().queueTask(doExpose)

        # wait doExpose to be scheduled
        time.sleep(1)        

        while cam.isExposing(): time.sleep(0.1)

        # rationale: first exposure will start and the next will wait,
        # so we can never get the second exposure beginning before exposure one readout finishes.
        assert len(begin_times) == 2
        assert len(end_times) == 2
        assert (end_times[1] > begin_times[0])
        
    def test_expose_abort (self):

        cam = self.manager.getProxy(Camera)

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(Camera)
            cam.expose(exp_time=600, filename="test_expose_abort.fits")
        
        self.manager.getPool().queueTask(doExpose)

        time.sleep(2)

        assert cam.isExposing() == True

        cam.abortExposure()

        assert cam.isExposing() == False

    def test_cooling (self):

        cam = self.manager.getProxy(Camera)

        cam.stopCooling()
        assert cam.isCooling() == False

        for i in range(10):
            print cam.getTemperature()
            time.sleep(0.5)

        cam.startCooling(0)
        assert cam.isCooling() == True

        while cam.getTemperature() > 0:
            print cam.getTemperature()
            time.sleep(1)

        cam.stopCooling()
        assert cam.isCooling() == False

        
