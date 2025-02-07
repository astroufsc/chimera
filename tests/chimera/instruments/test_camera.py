# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait

import pytest

import chimera.core.log
from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.core.exceptions import ChimeraValueError
from chimera.core.proxy import Proxy
from chimera.interfaces.camera import CameraStatus
from chimera.instruments.fakecamera import FakeCamera
from chimera.core.manager import Manager

chimera.core.log.setConsoleLevel(int(1e10))
log = logging.getLogger("chimera.tests")


# hack for event  triggering asserts
FiredEvents = {}


@pytest.fixture(scope="class")
def camera():
    manager = Manager()
    manager.addClass(FakeCamera, "fake")

    def exposeBeginClbk(request):
        FiredEvents["exposeBegin"] = (time.time(), request)

    def exposeCompleteClbk(request, status):
        FiredEvents["exposeComplete"] = (time.time(), request, status)

    def readoutBeginClbk(request):
        FiredEvents["readoutBegin"] = (time.time(), request)

    def readoutCompleteClbk(proxy, status):
        FiredEvents["readoutComplete"] = (time.time(), proxy, status)

    cam = manager.getProxy("/FakeCamera/fake")
    cam.exposeBegin += exposeBeginClbk
    cam.exposeComplete += exposeCompleteClbk
    cam.readoutBegin += readoutBeginClbk
    cam.readoutComplete += readoutCompleteClbk

    yield cam

    manager.shutdown()


@pytest.fixture()
def pool():
    p = ThreadPoolExecutor()
    yield p
    p.shutdown()


class TestCamera:
    def assertEvents(self, exposeStatus, readoutStatus):
        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        assert "exposeBegin" in FiredEvents
        assert isinstance(FiredEvents["exposeBegin"][1], ImageRequest)

        assert "exposeComplete" in FiredEvents
        assert FiredEvents["exposeComplete"][0] > FiredEvents["exposeBegin"][0]
        assert isinstance(FiredEvents["exposeComplete"][1], ImageRequest)
        assert FiredEvents["exposeComplete"][2] in CameraStatus
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

            assert FiredEvents["readoutComplete"][2] in CameraStatus
            assert FiredEvents["readoutComplete"][2] == readoutStatus

    def test_simple(self, camera):
        assert camera.isExposing() is False

    def test_single_expose(self, camera):
        frames = 0

        frames = camera.expose(
            exptime=2, frames=2, interval=0.5, filename="autogen-expose.fits"
        )

        assert len(frames) == 2
        assert isinstance(frames[0], Proxy)
        assert isinstance(frames[1], Proxy)

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)

    def test_expose_checks(self, camera):
        # exp_time ranges
        with pytest.raises(ChimeraValueError):
            camera.expose(exptime=-1)
        with pytest.raises(ChimeraValueError):
            camera.expose(exptime=1e100)

        # frame ranges
        with pytest.raises(ChimeraValueError):
            camera.expose(exptime=1, frames=0)
        with pytest.raises(ChimeraValueError):
            camera.expose(exptime=1, frames=-1)

        # interval ranges
        with pytest.raises(ChimeraValueError):
            camera.expose(exptime=0, interval=-1)

        # compression
        camera.expose(exptime=0, compress_format="fits_rice")

    def test_expose_lock(self, camera, pool):
        begin_times = []
        end_times = []

        def exposeBeginClbk(request):
            begin_times.append(time.time())

        def readoutCompleteClbk(request, status):
            end_times.append(time.time())

        camera.exposeBegin += exposeBeginClbk
        camera.readoutComplete += readoutCompleteClbk

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            # cam = manager.getProxy(self.CAMERA)
            camera.expose(exptime=2, filename="autogen-expose-lock.fits")

        e1 = pool.submit(doExpose)
        e2 = pool.submit(doExpose)

        # wait doExpose to be scheduled
        time.sleep(1)

        while len(end_times) < 2:
            time.sleep(1)

        # rationale: first exposure will start and the next will wait,
        # so we can never get the second exposure beginning before exposure one readout finishes.
        assert len(begin_times) == 2
        assert len(end_times) == 2
        assert end_times[1] > begin_times[0]

        wait([e1, e2], timeout=10)

        self.assertEvents(CameraStatus.OK, CameraStatus.OK)

    def test_expose_abort(self, camera, pool):
        print()

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            # cam = self.manager.getProxy(self.CAMERA)
            camera.expose(exptime=10, filename="autogen-expose-abort.fits")

        #
        # abort exposure while exposing
        #

        exposure = pool.submit(doExpose)

        # thread scheduling
        time.sleep(2)

        assert camera.isExposing() is True
        camera.abortExposure()
        assert camera.isExposing() is False

        wait([exposure], timeout=10)

        self.assertEvents(CameraStatus.ABORTED, False)

    def test_readout_abort(self, camera, pool):
        exposeComplete = threading.Event()

        print()

        def doExpose():
            # need to get another Proxy as Proxies cannot be shared among threads
            # cam = manager.getProxy(self.CAMERA)
            camera.expose(exptime=5, filename="autogen-readout-abort.fits")

        def exposeCompleteCallback(request, status):
            exposeComplete.set()

        camera.exposeComplete += exposeCompleteCallback

        #
        # abort exposure while reading out
        #

        exposure = pool.submit(doExpose)

        # thread scheduling
        time.sleep(2)

        assert camera.isExposing() is True

        while not exposeComplete.is_set():
            time.sleep(0.1)

        assert camera.isExposing() is True
        camera.abortExposure()
        assert camera.isExposing() is False

        wait([exposure], timeout=10)

        self.assertEvents(CameraStatus.OK, CameraStatus.ABORTED)

    def test_cooling(self, camera):
        def eps_equal(a, b, eps):
            return abs(a - b) <= eps

        camera.stopCooling()
        assert camera.isCooling() is False

        cool = 10
        camera.startCooling(cool)
        assert camera.isCooling() is True

        print()
        while not eps_equal(camera.getTemperature(), cool, 0.25):
            print(f"\rwaiting to cool to {cool} oC: {camera.getTemperature()}", end=" ")
            sys.stdout.flush()
            time.sleep(1)

        camera.stopCooling()
        assert camera.isCooling() is False
