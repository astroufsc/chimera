"""Owning a child process: start it, notice it died, leave nothing behind.

No chimera controller had spawned a child before this one, so every rule the
class relies on gets a test — including the ones that are only wrong at 3am,
like an orphan surviving shutdown.
"""

import logging
import os
import signal
import subprocess
import time

import pytest

from chimera.controllers.videostreamer.core import Go2rtcProcess, generate_config

CAMERAS = {
    "dome": "rtsp://user:pass@10.0.0.1/stream",
    "allsky": "ffmpeg:device?video=0",
}


def _running(pid: int) -> bool:
    """Alive and executing — a zombie is not.

    A process abandoned inside this test is still pytest's child, so it stays
    reapable-but-dead until someone wait()s it, and os.kill(pid, 0) keeps
    succeeding. `ps` state Z is the distinction that matters.
    """
    state = subprocess.run(
        ["ps", "-p", str(pid), "-o", "state="], capture_output=True, text=True
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


@pytest.fixture
def proc(fake_go2rtc, free_port):
    yaml_text = generate_config(
        cameras=CAMERAS, video_host="127.0.0.1", video_port=free_port
    )
    process = Go2rtcProcess(fake_go2rtc, yaml_text, free_port)
    yield process
    process.stop()


class TestStart:
    def test_start_waits_for_the_api_not_just_the_pid(self, proc):
        """ "the process exists" is not "the relay works" — a binary that dies
        on its own config leaves a Popen that looks fine for a moment."""
        proc.start()

        assert proc.is_alive()
        assert proc.probe() is not None

    def test_the_generated_config_is_on_disk_while_it_runs(self, proc):
        proc.start()

        assert proc.config_path is not None
        with open(proc.config_path) as fp:
            assert "dome" in fp.read()

    def test_probe_reports_the_configured_cameras(self, proc):
        proc.start()

        assert set(proc.probe()) == set(CAMERAS)

    def test_a_binary_that_exits_at_once_is_reported_not_awaited(
        self, dying_go2rtc, free_port
    ):
        process = Go2rtcProcess(
            dying_go2rtc, "api:\n  listen: '127.0.0.1:1'\n", free_port
        )

        with pytest.raises(RuntimeError, match="exited immediately with code 3"):
            process.start(timeout=10)

    def test_a_binary_that_never_answers_times_out(self, mute_go2rtc, free_port):
        process = Go2rtcProcess(
            mute_go2rtc, "api:\n  listen: '127.0.0.1:1'\n", free_port
        )

        with pytest.raises(RuntimeError, match="did not answer"):
            process.start(timeout=1.0)

        process.stop()


class TestStop:
    def test_stop_leaves_no_child_and_no_config(self, proc):
        proc.start()
        assert os.path.exists(proc.config_path)

        proc.stop()

        assert not proc.is_alive()
        # the generated config and the pidfile go with it — a leftover pidfile
        # would make the next start hunt a process that never existed
        assert not os.path.exists(proc.config_path)
        assert not os.path.exists(proc._pid_path)

    def test_stop_is_idempotent(self, proc):
        proc.start()
        proc.stop()
        proc.stop()  # must not raise

    def test_stop_tolerates_a_child_that_is_already_gone(self, proc):
        """The child stays in chimera's process group on purpose, so a terminal
        ctrl-c reaches it first. __stop__ then finds a corpse, and that is
        normal, not an error."""
        proc.start()
        proc._proc.kill()
        proc._proc.wait(timeout=5)

        proc.stop()  # must not raise

    def test_no_orphan_survives(self, proc):
        proc.start()
        pid = proc._proc.pid

        proc.stop()

        # the pid must be reaped, not merely signalled
        result = subprocess.run(["ps", "-p", str(pid)], capture_output=True, text=True)
        assert str(pid) not in result.stdout


class TestStaleRelay:
    """chimera killed without unwinding leaves a relay holding the port.

    Reproduced for real: SIGTERM to the supervising process skips __stop__
    entirely, and go2rtc went on serving the old config while the next start
    would have failed with "address in use" — video that works, from a
    configuration nobody can see.
    """

    def test_a_survivor_is_reaped_by_the_next_start(self, fake_go2rtc, free_port):
        yaml_text = generate_config(
            cameras=CAMERAS, video_host="127.0.0.1", video_port=free_port
        )

        abandoned = Go2rtcProcess(fake_go2rtc, yaml_text, free_port)
        abandoned.start()
        orphan = abandoned._proc.pid
        # walk away without stop(), the way a SIGKILLed supervisor does
        abandoned._proc = None

        successor = Go2rtcProcess(fake_go2rtc, yaml_text, free_port)
        try:
            # start() only returns once the API answers, so a successor that
            # comes up on the same port is proof the orphan let go of it
            successor.start()
            assert successor.is_alive()
            assert successor._proc.pid != orphan
            assert not _running(orphan)
        finally:
            successor.stop()
            # this test deliberately abandons a process; if the reap it is
            # testing ever regresses, the suite must not leak one per run
            if _running(orphan):
                os.kill(orphan, signal.SIGKILL)

    def test_only_a_go2rtc_is_ever_signalled(self, fake_go2rtc, free_port, tmp_path):
        """Pids are recycled. Killing whatever inherited one would be much
        worse than the stale relay we are trying to clean up."""
        proc = Go2rtcProcess(fake_go2rtc, "", free_port)

        os.makedirs(proc._dir, exist_ok=True)
        # our own pid: alive, and emphatically not a go2rtc
        with open(proc._pid_path, "w") as fp:
            fp.write(str(os.getpid()))

        assert proc.reap_stale() is None
        os.kill(os.getpid(), 0)  # still here

    def test_no_pidfile_is_not_an_error(self, fake_go2rtc, free_port):
        proc = Go2rtcProcess(fake_go2rtc, "", free_port)

        assert proc.reap_stale() is None


class TestLogPump:
    """go2rtc's own log must reach chimera's, or a black tile has no evidence.

    This was stdout=DEVNULL. Every diagnosis in this module — the RTSP bind
    clash, "no route to host", ffmpeg's unsupported-framerate complaint — was
    already being printed by the relay and thrown away, so an operator staring
    at a black feed had nothing to read.
    """

    def test_a_relay_line_reaches_the_python_logger(self, talkative_go2rtc, free_port):
        records: list[logging.LogRecord] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger = logging.getLogger("chimera.controllers.videostreamer.core")
        handler = Capture()
        level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        yaml_text = generate_config(
            cameras=CAMERAS, video_host="127.0.0.1", video_port=free_port
        )
        proc = Go2rtcProcess(talkative_go2rtc, yaml_text, free_port)
        try:
            proc.start(timeout=10)

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if any("hello from the relay" in r.getMessage() for r in records):
                    break
                time.sleep(0.05)
            else:
                pytest.fail(
                    f"relay output never logged; saw {[r.getMessage() for r in records]}"
                )
        finally:
            proc.stop()
            logger.removeHandler(handler)
            logger.setLevel(level)

    def test_an_err_line_is_raised_to_warning(self, talkative_go2rtc, free_port):
        """go2rtc tags its own severity; a wedged relay should not hide in debug."""
        records: list[logging.LogRecord] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger = logging.getLogger("chimera.controllers.videostreamer.core")
        handler = Capture()
        level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        yaml_text = generate_config(
            cameras=CAMERAS, video_host="127.0.0.1", video_port=free_port
        )
        proc = Go2rtcProcess(talkative_go2rtc, yaml_text, free_port)
        try:
            proc.start(timeout=10)

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                err = [r for r in records if "something went wrong" in r.getMessage()]
                if err:
                    assert err[0].levelno == logging.WARNING
                    break
                time.sleep(0.05)
            else:
                pytest.fail("the ERR line never arrived")
        finally:
            proc.stop()
            logger.removeHandler(handler)
            logger.setLevel(level)


class TestLiveness:
    def test_a_dead_child_is_not_alive(self, proc):
        proc.start()
        proc._proc.kill()
        proc._proc.wait(timeout=5)

        assert not proc.is_alive()
        assert proc.returncode() is not None

    def test_probe_returns_none_rather_than_raising_when_nothing_answers(
        self, fake_go2rtc, free_port
    ):
        """probe() runs on the control loop. A wedged relay must not take the
        loop down with it, so a failure is None, never an exception."""
        process = Go2rtcProcess(fake_go2rtc, "", free_port)

        assert process.probe(timeout=0.5) is None
