# SPDX-License-Identifier: GPL-2.0-or-later
# End-to-end regression tests for scheduler stop semantics (lna40 incident,
# opd-40 2026-07-25): a sched.stop() must actually stop the running program,
# including after a start() during BUSY re-queued the still-unfinished
# program — on master that spawned a second worker that outlived every stop
# and kept the camera exposing for 52 min behind a closed dome.

import time

import pytest

# the scheduler DB is redirected to a temp file in tests/chimera/conftest.py,
# before any module import binds the model engine
from chimera.controllers.imageserver.imageserver import ImageServer
from chimera.controllers.scheduler.controller import Scheduler
from chimera.controllers.scheduler.model import Expose, Program, Session
from chimera.controllers.scheduler.states import State
from chimera.core.site import Site
from chimera.instruments.fakecamera import FakeCamera
from chimera.instruments.fakefilterwheel import FakeFilterWheel


@pytest.fixture
def system(manager, wait_for, tmp_path):
    manager.add_class(Site, "fake")
    manager.add_class(
        ImageServer, "fake", {"images_dir": str(tmp_path), "httpd": False}
    )
    manager.add_class(FakeCamera, "fake")
    manager.add_class(FakeFilterWheel, "fake")
    manager.add_class(Scheduler, "fake")

    sched = manager.get_proxy("/Scheduler/0")
    camera = manager.get_proxy("/Camera/0")

    # wait for the controller's control() tick to start the machine thread
    assert wait_for(lambda: sched.state() is not None, 10)

    # a clean program table for each test
    session = Session()
    for program in session.query(Program).all():
        session.delete(program)
    session.commit()

    yield sched, camera, tmp_path


def add_program(tmp_path, frames=8, exptime=1):
    program = Program(name="stop-test", pi="tester")
    program.actions = [
        Expose(
            frames=frames,
            exptime=exptime,
            shutter="OPEN",
            image_type="object",
            object_name="stop-test",
            # absolute path: no ImageServer lookup surprises
            filename=str(tmp_path / "frame"),
        )
    ]
    session = Session()
    session.add(program)
    session.commit()


class TestSchedulerStop:
    def test_stop_single_worker(self, system, wait_for):
        """One worker, stop mid-multi-frame-expose stops for real."""
        sched, camera, tmp_path = system
        add_program(tmp_path)

        sched.start()
        assert wait_for(camera.is_exposing, 15), "exposure never started"

        sched.stop()

        assert wait_for(lambda: sched.state() == State.OFF, 10)
        assert not camera.is_exposing(), "camera still exposing after OFF"

        # and it must STAY stopped
        time.sleep(3)
        assert not camera.is_exposing(), "camera exposing again after stop"
        assert sched.state() == State.OFF

    def test_stop_after_restart_during_busy(self, system, wait_for):
        """The incident case: a start() while BUSY re-queues the unfinished
        program; the following stop must still kill everything and OFF must
        mean the camera is no longer being driven."""
        sched, camera, tmp_path = system
        # long enough that a surviving execution could not finish naturally
        # inside the assertion windows below (the incident program had 100s
        # of frames)
        add_program(tmp_path, frames=60, exptime=1)

        sched.start()
        assert wait_for(camera.is_exposing, 15), "exposure never started"

        # what robobs does when (re)submitting programs mid-night
        sched.start()
        time.sleep(1)

        sched.stop()

        assert wait_for(lambda: sched.state() == State.OFF, 10), (
            "machine never reached OFF after stop"
        )

        # OFF must be honest: the camera stops and STAYS stopped
        assert not camera.is_exposing(), (
            "camera still exposing after the scheduler reported OFF"
        )
        assert not wait_for(camera.is_exposing, 5), (
            "camera started exposing again after the stop (a second worker survived)"
        )
        assert sched.state() == State.OFF, "scheduler re-armed itself after stop"
