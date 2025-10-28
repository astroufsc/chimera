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
from chimera.util.image import Image

chimera.core.log.set_console_level(int(1e10))
log = logging.getLogger("chimera.tests")


# hack for event triggering asserts
fired_events = {}


@pytest.fixture(scope="class")
def camera():
    manager = Manager()
    manager.add_class(FakeCamera, "fake")

    def expose_begin_clbk(request):
        fired_events["expose_begin"] = (time.time(), request)

    def expose_complete_clbk(request, status):
        fired_events["expose_complete"] = (time.time(), request, status)

    def readout_begin_clbk(request):
        fired_events["readout_begin"] = (time.time(), request)

    def readout_complete_clbk(proxy, status):
        fired_events["readout_complete"] = (time.time(), proxy, status)

    cam = manager.get_proxy("/FakeCamera/fake")
    cam.expose_begin += expose_begin_clbk
    cam.expose_complete += expose_complete_clbk
    cam.readout_begin += readout_begin_clbk
    cam.readout_complete += readout_complete_clbk

    yield cam

    manager.shutdown()


@pytest.fixture()
def pool():
    p = ThreadPoolExecutor()
    yield p
    p.shutdown()


class TestCamera:
    def assert_events(self, expose_status, readout_status):
        # for every exposure, we need to check if all events were fired in the right order
        # and with the right parameters

        assert "expose_begin" in fired_events
        assert isinstance(fired_events["expose_begin"][1], ImageRequest)

        assert "expose_complete" in fired_events
        assert fired_events["expose_complete"][0] > fired_events["expose_begin"][0]
        assert isinstance(fired_events["expose_complete"][1], ImageRequest)
        assert fired_events["expose_complete"][2] in CameraStatus
        assert fired_events["expose_complete"][2] == expose_status

        if readout_status:
            assert "readout_begin" in fired_events
            assert fired_events["readout_begin"][0] > fired_events["expose_complete"][0]
            assert isinstance(fired_events["readout_begin"][1], ImageRequest)

            assert "readout_complete" in fired_events
            assert (
                fired_events["readout_complete"][0] > fired_events["readout_begin"][0]
            )
            if readout_status == CameraStatus.OK:
                assert isinstance(fired_events["readout_complete"][1], Image)
            else:
                assert fired_events["readout_complete"][1] is None

            assert fired_events["readout_complete"][2] in CameraStatus
            assert fired_events["readout_complete"][2] == readout_status

    def test_simple(self, camera):
        assert camera.is_exposing() is False

    def test_single_expose(self, camera):
        frames = camera.expose(
            exptime=2, frames=2, interval=0.5, filename="autogen-expose.fits"
        )

        assert len(frames) == 2
        assert isinstance(frames[0], Image)
        assert isinstance(frames[1], Image)

        self.assert_events(CameraStatus.OK, CameraStatus.OK)

    def test_expose_checks(self, camera):
        # exp_time ranges
        with pytest.raises(Exception) as excinfo:
            camera.expose(exptime=-1)
        assert "ChimeraValueError" in str(excinfo.value)

        with pytest.raises(Exception) as excinfo:
            camera.expose(exptime=1e100)
        assert "ChimeraValueError" in str(excinfo.value)

        # frame ranges
        with pytest.raises(Exception) as excinfo:
            camera.expose(exptime=1, frames=0)
        assert "ChimeraValueError" in str(excinfo.value)

        with pytest.raises(Exception) as excinfo:
            camera.expose(exptime=1, frames=-1)
        assert "ChimeraValueError" in str(excinfo.value)

        # interval ranges
        with pytest.raises(Exception) as excinfo:
            camera.expose(exptime=0, interval=-1)
        assert "ChimeraValueError" in str(excinfo.value)

        # compression
        camera.expose(exptime=0, compress_format="fits_rice")

    def test_expose_lock(self, camera, pool):
        begin_times = []
        end_times = []

        def expose_begin_clbk(request):
            begin_times.append(time.time())

        def readout_complete_clbk(request, status):
            end_times.append(time.time())

        camera.expose_begin += expose_begin_clbk
        camera.readout_complete += readout_complete_clbk

        def do_expose():
            camera.expose(exptime=2, filename="autogen-expose-lock.fits")

        e1 = pool.submit(do_expose)
        e2 = pool.submit(do_expose)

        # wait do_expose to be scheduled
        time.sleep(1)

        while len(end_times) < 2:
            time.sleep(1)

        # rationale: first exposure will start and the next will wait,
        # so we can never get the second exposure beginning before exposure one readout finishes.
        assert len(begin_times) == 2
        assert len(end_times) == 2
        assert end_times[1] > begin_times[0]

        wait([e1, e2], timeout=10)

        self.assert_events(CameraStatus.OK, CameraStatus.OK)

    def test_expose_abort(self, camera, pool):
        print()

        def do_expose():
            camera.expose(exptime=10, filename="autogen-expose-abort.fits")

        #
        # abort exposure while exposing
        #

        exposure = pool.submit(do_expose)

        # thread scheduling
        time.sleep(2)

        assert camera.is_exposing() is True
        camera.abort_exposure()
        assert camera.is_exposing() is False

        wait([exposure], timeout=10)

        self.assert_events(CameraStatus.ABORTED, False)

    @pytest.mark.skip(reason="test still needs work. abort flow is not well defined")
    def test_readout_abort(self, camera, pool):
        expose_complete = threading.Event()

        print()

        def do_expose():
            camera.expose(exptime=5, filename="autogen-readout-abort.fits")

        def expose_complete_callback(request, status):
            expose_complete.set()

        camera.expose_complete += expose_complete_callback

        #
        # abort exposure while reading out
        #

        exposure = pool.submit(do_expose)

        # thread scheduling
        time.sleep(2)

        assert camera.is_exposing() is True

        while not expose_complete.is_set():
            time.sleep(0.1)

        assert camera.is_exposing() is True
        camera.abort_exposure()
        assert camera.is_exposing() is False

        wait([exposure], timeout=10)

        self.assert_events(CameraStatus.OK, CameraStatus.ABORTED)

    def test_cooling(self, camera):
        def eps_equal(a, b, eps):
            return abs(a - b) <= eps

        camera.stop_cooling()
        assert camera.is_cooling() is False

        cool = 10
        camera.start_cooling(cool)
        assert camera.is_cooling() is True

        print()
        while not eps_equal(camera.get_temperature(), cool, 0.25):
            print(
                f"\rwaiting to cool to {cool} oC: {camera.get_temperature()}", end=" "
            )
            sys.stdout.flush()
            time.sleep(1)

        camera.stop_cooling()
        assert camera.is_cooling() is False
