# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>




from concurrent.futures import ThreadPoolExecutor
import time
import logging
import sys
import threading

from chimera.core.manager import Manager
from chimera.core.exceptions import ChimeraValueError
from chimera.core.proxy import Proxy

from chimera.controllers.imageserver.imagerequest import ImageRequest

from chimera.interfaces.camera import CameraStatus

from chimera.util.enum import EnumValue

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

import chimera.core.log
import pytest

chimera.core.log.setConsoleLevel(int(1e10))
log = logging.getLogger("chimera.tests")


# hack for event  triggering asserts
FiredEvents = {}


class CameraTest(object):

    manager = None
    CAMERA = ""

    def assertEvents(self, exposeStatus, readoutStatus):

        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        assert "exposeBegin" in FiredEvents
        assert isinstance(FiredEvents["exposeBegin"][1], ImageRequest)

        assert "exposeComplete" in FiredEvents
        assert FiredEvents["exposeComplete"][0] > FiredEvents["exposeBegin"][0]
        assert isinstance(FiredEvents["exposeComplete"][1], ImageRequest)
        assert (
            isinstance(FiredEvents["exposeComplete"][2], EnumValue)
            and FiredEvents["exposeComplete"][2] in CameraStatus
        )
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

            assert (
                isinstance(FiredEvents["readoutComplete"][2], EnumValue)
                and FiredEvents["readoutComplete"][2] in CameraStatus
            )
            assert FiredEvents["readoutComplete"][2] == readoutStatus

    def setupEvents(self):

        def exposeBeginClbk(request):
            FiredEvents["exposeBegin"] = (time.time(), request)

        def exposeCompleteClbk(request, status):
            FiredEvents["exposeComplete"] = (time.time(), request, status)

        def readoutBeginClbk(request):
            FiredEvents["readoutBegin"] = (time.time(), request)

        def readoutCompleteClbk(proxy, status):
            FiredEvents["readoutComplete"] = (time.time(), proxy, status)

        cam = self.manager.getProxy(self.CAMERA)
        cam.exposeBegin += exposeBeginClbk
        cam.exposeComplete += exposeCompleteClbk
        cam.readoutBegin += readoutBeginClbk
        cam.readoutComplete += readoutCompleteClbk

    def test_simple(self):

        cam = self.manager.getProxy(self.CAMERA)
        assert cam.isExposing() is False

    def test_expose(self):

        cam = self.manager.getProxy(self.CAMERA)

        frames = 0

        try:
            frames = cam.expose(
                exptime=2, frames=2, interval=0.5, filename="autogen-expose.fits"
            )
        except Exception:
            log.exception("problems")

        assert len(frames) == 2
        assert isinstance(frames[0], Proxy)
        assert isinstance(frames[1], Proxy)

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)

    def test_expose_checkings(self):

        cam = self.manager.getProxy(self.CAMERA)

        # exp_time ranges
        with pytest.raises(ChimeraValueError):
            cam.expose(exptime=-1)
        with pytest.raises(ChimeraValueError):
            cam.expose(exptime=1e100)

        # frame ranges
        with pytest.raises(ChimeraValueError):
            cam.expose(exptime=1, frames=0)
        with pytest.raises(ChimeraValueError):
            cam.expose(exptime=1, frames=-1)

        # interval ranges
        with pytest.raises(ChimeraValueError):
            cam.expose(exptime=0, interval=-1)

        # compression
        cam.expose(exptime=0, compress_format="fits_rice")

    def test_expose_lock(self):

        cam = self.manager.getProxy(self.CAMERA)

        begin_times = []
        end_times = []

        def exposeBeginClbk(request):
            begin_times.append(time.time())

        def readoutCompleteClbk(request, status):
            end_times.append(time.time())

        cam.exposeBegin += exposeBeginClbk
        cam.readoutComplete += readoutCompleteClbk

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=2, filename="autogen-expose-lock.fits")

        pool = ThreadPoolExecutor()
        pool.submit(doExpose)
        pool.submit(doExpose)

        # wait doExpose to be scheduled
        time.sleep(1)

        while len(end_times) < 2:
            time.sleep(1)

        # rationale: first exposure will start and the next will wait,
        # so we can never get the second exposure beginning before exposure one readout finishes.
        assert len(begin_times) == 2
        assert len(end_times) == 2
        assert end_times[1] > begin_times[0]

        pool.

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)

    def test_expose_abort(self):

        cam = self.manager.getProxy(self.CAMERA)

        print()

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=10, filename="autogen-expose-abort.fits")

        #
        # abort exposure while exposing
        #

        pool = ThreadPoolExecutor()
        pool.queueTask(doExpose)

        # thread scheduling
        time.sleep(2)

        assert cam.isExposing() is True
        cam.abortExposure()
        assert cam.isExposing() is False

        pool.joinAll()

        self.assertEvents(CameraStatus.ABORTED, False)

    def test_readout_abort(self):

        cam = self.manager.getProxy(self.CAMERA)
        exposeComplete = threading.Event()

        print()

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            cam = self.manager.getProxy(self.CAMERA)
            cam.expose(exptime=5, filename="autogen-readout-abort.fits")

        def exposeCompleteCallback(request, status):
            exposeComplete.set()

        cam.exposeComplete += exposeCompleteCallback

        #
        # abort exposure while reading out
        #

        pool = ThreadPoolExecutor()
        pool.queueTask(doExpose)

        # thread scheduling
        time.sleep(2)

        assert cam.isExposing() is True

        while not exposeComplete.isSet():
            time.sleep(0.1)

        assert cam.isExposing() is True
        cam.abortExposure()
        assert cam.isExposing() is False

        pool.joinAll()

        self.assertEvents(CameraStatus.OK, CameraStatus.ABORTED)

    def test_cooling(self):

        cam = self.manager.getProxy(self.CAMERA)

        def eps_equal(a, b, eps):
            return abs(a - b) <= eps

        cam.stopCooling()
        assert cam.isCooling() is False

        cool = 10
        cam.startCooling(cool)
        assert cam.isCooling() is True

        print()
        while not eps_equal(cam.getTemperature(), cool, 0.25):
            print(f"\rwaiting to cool to {cool} oC: {cam.getTemperature()}", end=" ")
            sys.stdout.flush()
            time.sleep(1)

        cam.stopCooling()
        assert cam.isCooling() is False


#
# setup real and fake tests
#
class TestFakeCamera(FakeHardwareTest, CameraTest):

    def setup(self):
        self.manager = Manager(port=8000)
        from chimera.instruments.fakecamera import FakeCamera

        self.manager.addClass(FakeCamera, "fake")
        self.CAMERA = "/FakeCamera/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()


class TestRealCamera(RealHardwareTest, CameraTest):

    def setup(self):

        self.manager = Manager(port=8000)

        from chimera.instruments.sbig import SBIG

        self.manager.addClass(SBIG, "sbig")
        self.CAMERA = "/SBIG/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()
