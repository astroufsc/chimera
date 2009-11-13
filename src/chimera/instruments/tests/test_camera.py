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
import threading

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.threads  import ThreadPool
from chimera.core.exceptions import ChimeraValueError
from chimera.core.proxy import Proxy

from chimera.controllers.imageserver.imagerequest import ImageRequest

from chimera.interfaces.camera import CameraStatus

from chimera.util.enum import EnumValue

import chimera.core.log
chimera.core.log.setConsoleLevel(1e10)
log = logging.getLogger("chimera.tests")


from nose.tools import assert_raises

# hack for event  triggering asserts
FiredEvents = {}

class CameraTest (object):

    manager = None
    CAMERA = ''

    def assertEvents(self, exposeStatus, readoutStatus):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters
        
        assert "exposeBegin" in FiredEvents
        assert isinstance(FiredEvents["exposeBegin"][1], ImageRequest)

        assert "exposeComplete" in FiredEvents
        assert FiredEvents["exposeComplete"][0] > FiredEvents["exposeBegin"][0]
        assert isinstance(FiredEvents["exposeComplete"][1], ImageRequest)
        assert isinstance(FiredEvents["exposeComplete"][2], EnumValue) and FiredEvents["exposeComplete"][2] in CameraStatus
        assert FiredEvents["exposeComplete"][2] == exposeStatus

        if readoutStatus:

            assert "readoutBegin" in FiredEvents
            assert FiredEvents["readoutBegin"][0] > FiredEvents["exposeComplete"][0]
            assert isinstance(FiredEvents["readoutBegin"][1], ImageRequest)

            assert "readoutComplete" in FiredEvents
            assert FiredEvents["readoutComplete"][0] > FiredEvents["readoutBegin"][0]
            if readoutStatus == CameraStatus.OK:
                assert isinstance(FiredEvents["readoutComplete"][1], Proxy)
            else:
                assert isinstance(FiredEvents["readoutComplete"][1], type(None))
            
            assert isinstance(FiredEvents["readoutComplete"][2], EnumValue) and FiredEvents["readoutComplete"][2] in CameraStatus
            assert FiredEvents["readoutComplete"][2] == readoutStatus

    def setupEvents(self):

        @callback(self.manager)
        def exposeBeginClbk(request):
            FiredEvents["exposeBegin"] = (time.time(), request)

        @callback(self.manager)
        def exposeCompleteClbk(request, status):
            FiredEvents["exposeComplete"] = (time.time(), request, status)

        @callback(self.manager)
        def readoutBeginClbk(request):
            FiredEvents["readoutBegin"] = (time.time(), request)

        @callback(self.manager)
        def readoutCompleteClbk(proxy, status):
            FiredEvents["readoutComplete"] = (time.time(), proxy, status)

        cam = self.manager.getProxy(self.CAMERA)
        cam.exposeBegin     += exposeBeginClbk
        cam.exposeComplete  += exposeCompleteClbk        
        cam.readoutBegin    += readoutBeginClbk        
        cam.readoutComplete += readoutCompleteClbk
        
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

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)

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
        def readoutCompleteClbk(request, status):
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

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)        
        
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

        self.assertEvents(CameraStatus.ABORTED, False)

    def test_readout_abort (self):

        cam = self.manager.getProxy(self.CAMERA)
        exposeComplete = threading.Event()

        print
        
        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=5, filename="autogen-readout-abort.fits")

        @callback(self.manager)
        def exposeCompleteCallback(request, status):
            exposeComplete.set()

        cam.exposeComplete += exposeCompleteCallback

        #
        # abort exposure while reading out
        #

        pool = ThreadPool()
        pool.queueTask(doExpose)

        # thread scheduling
        time.sleep(2)

        assert cam.isExposing() == True

        while not exposeComplete.isSet():
            time.sleep(0.1)

        assert cam.isExposing() == True
        cam.abortExposure()
        assert cam.isExposing() == False

        pool.joinAll()

        self.assertEvents(CameraStatus.OK, CameraStatus.ABORTED)
        

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


#
# setup real and fake tests
#

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

class TestFakeCamera(FakeHardwareTest, CameraTest):

    def setup (self):
        self.manager = Manager(port=8000)
        from chimera.instruments.fakecamera import FakeCamera
        self.manager.addClass(FakeCamera, "fake")
        self.CAMERA = "/FakeCamera/0"

        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()
    
class TestRealCamera(RealHardwareTest, CameraTest):
    
    def setup (self):

        self.manager = Manager(port=8000)

        from chimera.instruments.sbig import SBIG
        self.manager.addClass(SBIG, "sbig")
        self.CAMERA = "/SBIG/0"

        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()
