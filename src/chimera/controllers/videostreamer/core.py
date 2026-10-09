# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""Config generation and process supervision for go2rtc.

Split out of the controller so the generator can be tested as what it is — a
pure function, config in, YAML out — without a manager, a bus or a binary. It
is the part most likely to be quietly wrong: a relay that starts happily with
the wrong listen address looks identical to one that started right, until a
browser on another host tries to dial it.
"""

import json
import logging
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request

import yaml

from chimera.core.exceptions import ChimeraException

log = logging.getLogger(__name__)


class Go2rtcNotFoundException(ChimeraException):
    """The binary is not where we were told to look."""


def free_port() -> int:
    """A port nothing is listening on right now.

    Used for go2rtc's RTSP listener, which is pure internal plumbing: every
    `ffmpeg:` source works by spawning ffmpeg and publishing into go2rtc's own
    RTSP server, so the port must exist — but nothing outside chimera dials it,
    because the browser reaches feeds over WHEP, WebSocket, HLS or MJPEG.

    Binding the documented 8554 was actively harmful. Anything else already
    holding it — most obviously another go2rtc, which is exactly what someone
    working on cameras has running — makes the listener fail, and go2rtc then
    logs "rtsp module disabled" and quietly serves *nothing* from any ffmpeg
    source while its HTTP API answers normally. Measured: every ffmpeg source
    returned 0 bytes with the API reporting a healthy relay.

    Inherently racy — the port is free when we look and could be taken before
    go2rtc binds it — but the window is milliseconds and the failure is loud
    and retried, whereas a fixed port collides deterministically and silently.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def generate_config(
    *,
    cameras: dict,
    video_host: str = "0.0.0.0",
    video_port: int = 1984,
    rtsp_port: int = 8554,
    webrtc: bool = True,
    webrtc_port: int = 8555,
    public_host: str = "localhost",
) -> str:
    """Render the go2rtc YAML. Pure: no filesystem, no clock, no network.

    Everything go2rtc-shaped is decided here so that nobody has to configure
    go2rtc — it is a backend, not a second product to learn. What the operator
    writes in chimera.config is a camera list, where to listen and what the
    browser should dial; candidates, codec templates and auth are ours.

    The listen addresses are written out explicitly even where they match
    go2rtc's own defaults: these are Chimera-managed ports now, and a config
    file that names them is a config file you can read to find out.
    """
    config: dict = {
        "api": {
            "listen": f"{video_host}:{video_port}",
            # Without this go2rtc answers 403 to the WebSocket upgrade and every
            # feed is black — measured, not guessed. Its default rejects
            # cross-origin upgrades, and the Chimera web app is *always* a
            # different origin: the relay is on 1984 and the app is on a dev
            # server, a static host, or anywhere else. This is precisely the
            # class of go2rtc detail an operator should never have to discover,
            # which is the reason we generate this file at all.
            #
            # "*" inherits the posture the rest of the stack already has — the
            # bus, the gateway and the pixel stream are equally unauthenticated
            # on a trusted network (see controllers/ws/README.md). It is not a
            # new exception; it would be one to leave the video broken instead.
            "origin": "*",
        },
        "rtsp": {"listen": f"{video_host}:{rtsp_port}"},
    }

    if webrtc:
        # candidates is the whole reason public_host exists: ICE advertises an
        # address the *browser* must reach, which is never 0.0.0.0 and is only
        # accidentally localhost.
        config["webrtc"] = {
            "listen": f"{video_host}:{webrtc_port}",
            "candidates": [f"{public_host}:{webrtc_port}"],
        }

    # last, so a human opening the file sees the cameras without scrolling
    config["streams"] = dict(cameras)

    return yaml.safe_dump(config, sort_keys=False, default_flow_style=False)


def resolve_binary(configured: str | None) -> str:
    """Find go2rtc, or say clearly where we looked.

    It is a binary on PATH, not a Python dependency, so `uv sync` and the wheel
    stay clean — at the cost of it being possible to not have it. There is no
    Homebrew formula: it ships as a zip from the GitHub releases page, and on
    macOS an unsigned download needs its quarantine attribute cleared.
    """
    if configured:
        if os.path.isfile(configured) and os.access(configured, os.X_OK):
            return configured
        raise Go2rtcNotFoundException(
            f"go2rtc_bin points at {configured!r}, which is not an executable file"
        )

    found = shutil.which("go2rtc")
    if found:
        return found

    raise Go2rtcNotFoundException(
        "go2rtc is not on PATH and go2rtc_bin is unset. It is a single static "
        "binary from https://github.com/AlexxIT/go2rtc/releases (no Homebrew "
        "formula); download it, chmod +x, and either put it on PATH or set "
        "go2rtc_bin to its full path. Video streams stay offline until then."
    )


class Go2rtcProcess:
    """Owns one go2rtc child: its config file, its lifetime, its liveness.

    No controller in chimera had spawned a child process before this one, so
    the rules are worth stating. The child stays in Chimera's process group on
    purpose — a ctrl-c in a terminal should stop the relay too — which means
    __stop__ will often find it already dead, and that is not an error.
    """

    def __init__(self, binary: str, config_yaml: str, video_port: int):
        self.binary = binary
        self.config_yaml = config_yaml
        self.video_port = video_port
        self._proc: subprocess.Popen | None = None
        # a *stable* directory, keyed by port, rather than mkdtemp: it is what
        # lets a fresh start find the pid a killed predecessor left behind. Two
        # relays on one port could not coexist anyway.
        self._dir = os.path.join(tempfile.gettempdir(), f"chimera-go2rtc-{video_port}")
        self.config_path = os.path.join(self._dir, "go2rtc.yaml")
        self._pid_path = os.path.join(self._dir, "go2rtc.pid")

    # -- lifecycle ---------------------------------------------------------

    def start(self, timeout: float = 10.0) -> None:
        """Spawn, then wait until the API answers.

        Waiting is what turns "the process exists" into "the relay works": a
        binary that dies on a bad config, or a port already in use, both leave
        a Popen that looks fine for a moment.
        """
        self.reap_stale()

        if self.probe(timeout=1.0) is not None:
            # Something is already answering on our port and it is not a relay
            # we left behind. Worth saying out loud, because the wait below
            # would otherwise be satisfied by *its* API and we would report a
            # healthy start while our own child died of "address in use" —
            # video that works, from a config nobody can see.
            log.warning(
                f"something is already serving port {self.video_port}; "
                f"go2rtc will not be able to bind it"
            )

        os.makedirs(self._dir, exist_ok=True)
        with open(self.config_path, "w") as fp:
            fp.write(self.config_yaml)

        # no start_new_session: stay in the process group, see the class docstring
        self._proc = subprocess.Popen(
            [self.binary, "-config", self.config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line buffered: a wedged relay still reports as it wedges
        )
        with open(self._pid_path, "w") as fp:
            fp.write(str(self._proc.pid))

        self._start_log_pump(self._proc)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"go2rtc exited immediately with code {self._proc.returncode} — "
                    f"check the generated config at {self.config_path}"
                )
            if self.probe() is not None:
                return
            time.sleep(0.1)

        raise RuntimeError(
            f"go2rtc did not answer on port {self.video_port} within {timeout:.0f}s"
        )

    def _start_log_pump(self, proc: subprocess.Popen) -> None:
        """Forward go2rtc's own log into chimera's, one line at a time.

        This used to be stdout=DEVNULL, and everything the relay had to say
        about itself went to the bit bucket. Every hard-won diagnosis in this
        module was already being printed and thrown away:

            ERR [rtsp] listen error="listen tcp :8554: bind: address already in use"
            ERR ... error="streams: exec: rtsp module disabled"
            ERR ... error="streams: dial tcp 192.168.0.247:554: no route to host"
            [in#0] Selected framerate (29.970030) is not supported by the device.

        An operator staring at a black tile could not see any of it. go2rtc
        tags its own lines with a level, so ERR/WRN are raised to warning and
        the rest stay at debug — a relay logs a handful of lines at startup and
        then goes quiet, so this is not chatty in steady state.
        """

        def pump() -> None:
            try:
                assert proc.stdout is not None
                for line in proc.stdout:
                    line = line.rstrip()
                    if not line:
                        continue
                    if " ERR " in line or " WRN " in line:
                        log.warning(f"go2rtc: {line}")
                    else:
                        log.debug(f"go2rtc: {line}")
            except (ValueError, OSError):
                pass  # the pipe closed under us: the child is gone, which is fine

        threading.Thread(target=pump, name="chimera-go2rtc-log", daemon=True).start()

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    log.warning("go2rtc ignored SIGKILL; leaving it")

        shutil.rmtree(self._dir, ignore_errors=True)

    def reap_stale(self) -> int | None:
        """Kill a relay a previous run left behind. Returns the pid it killed.

        __stop__ handles the ordinary exits, including ctrl-c — the child is in
        chimera's process group, so the terminal's SIGINT reaches it directly.
        What it cannot handle is chimera dying without unwinding: SIGKILL, an
        OOM kill, a `kill` from a script. Then go2rtc survives, holds the port,
        and the next start fails with "address in use" *while the stale relay
        keeps serving the old config* — video that works, from a configuration
        nobody can see. Measured: killing the supervisor with SIGTERM left
        exactly this.

        Only a pid we wrote ourselves is ever signalled, and only after its
        command line still names the exact binary we spawn — pids are recycled,
        and killing whatever inherited one would be far worse than a stale
        relay. The full command line rather than `ps -o comm=`, which reports
        the interpreter for anything script-shaped.
        """
        try:
            with open(self._pid_path) as fp:
                pid = int(fp.read().strip())
        except (OSError, ValueError):
            return None

        try:
            cmdline = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

        if not cmdline or self.binary not in cmdline:
            return None

        log.warning(f"reaping a go2rtc left behind by a previous run (pid {pid})")
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    return pid
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        return pid

    # -- supervision -------------------------------------------------------

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def returncode(self) -> int | None:
        return self._proc.poll() if self._proc is not None else None

    def probe(self, timeout: float = 2.0) -> dict | None:
        """GET /api/streams, or None if it did not answer.

        Short timeout on purpose: this runs on the control loop, and a relay
        that has wedged must not take the loop down with it.
        """
        url = f"http://127.0.0.1:{self.video_port}/api/streams"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return json.loads(response.read())
        except (urllib.error.URLError, OSError, ValueError, TimeoutError):
            return None
