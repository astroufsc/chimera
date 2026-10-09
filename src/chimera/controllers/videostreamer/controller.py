# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""VideoStreamer: the dome, all-sky and weather cameras, in a browser.

Monitoring cameras are ordinary RTSP/ONVIF boxes and UVC webcams. No science
comes off them, nothing in the observing loop reads them, and putting their
H.264 through CHZ1 would cost CPU to *increase* bitrate and lose the colour —
see docs/plans/streaming/monitoring-cameras.md for why this is a second
pipeline rather than a mode of the first.

So Chimera writes no camera driver and no codec. go2rtc does the relaying; this
controller generates its config from chimera.config, supervises it as a child
process, and publishes descriptors over the existing WS gateway. go2rtc is an
implementation detail nobody configures directly.

Declare it in chimera.config beside the gateway:

    controller:
      - type: VideoStreamer
        name: site
        public_host: default
        cameras:
          dome:   "rtsp://USER:PASS@CAMERA-HOST:554/Streaming/channels/101"
          allsky: "ffmpeg:device?video=0&video_size=1280x720&framerate=30#video=h264"

On the source strings, both learned the hard way. An IP camera is passthrough:
no "#video=" suffix, so its ASIC's H.264 goes to the browser untouched. A UVC
webcam must be transcoded, and on macOS it must ALSO carry video_size and
framerate — without them ffmpeg asks avfoundation for 29.97 fps, avfoundation
offers only 30.000030, and the source produces nothing at all while go2rtc
reports the stream as available.

Note what is *not* here: it opens no socket of its own. The pixel streamer
runs a WebSocket server because it produces pixels; this one produces nothing, it
answers stream_info(). There is no fourth chimera port — but go2rtc's 1984 and
8555 become Chimera-managed ports, and belong in the port convention. Its RTSP
port is not in that list on purpose: see rtsp_port below.

The split mirrors WsGateway/GatewayCore: this class is lifecycle and
configuration, core.py owns generation and the child process.
"""

import time

from chimera.controllers.videostreamer.core import (
    Go2rtcNotFoundException,
    Go2rtcProcess,
    free_port,
    generate_config,
    resolve_binary,
)
from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.streamer import Streamer, StreamKind

#: how long a restart backs off, doubling, after a child dies
BACKOFF_MIN = 2.0
BACKOFF_MAX = 60.0


class VideoStreamer(ChimeraObject, Streamer):
    __config__ = {
        # where go2rtc binds
        "video_host": "0.0.0.0",
        # the video API: MSE, HLS, MJPEG, snapshots, WebRTC signalling, WebUI
        "video_port": 1984,
        # go2rtc's internal RTSP server, which every ffmpeg: source publishes
        # into. 0 means "pick a free one", which is the right default because
        # nothing outside chimera dials it — and a fixed 8554 collides silently
        # with any other go2rtc on the host, killing every ffmpeg source while
        # the API still reports healthy. Set a real port only if you want a
        # dialable RTSP endpoint.
        "rtsp_port": 0,
        # the sub-second path; False drops every viewer to MSE, which is the
        # right default for a dashboard anyway
        "webrtc": True,
        "webrtc_port": 8555,
        # what the browser dials, as opposed to what we bind: "default"
        # resolves to the bus host at __start__, as ImageServer does
        "public_host": "default",
        # name -> go2rtc source string. The one field that stays go2rtc-shaped:
        # it is where the per-site knowledge lives, it is well documented
        # upstream, and a Chimera dialect in front of it would have nothing to
        # translate. Names matter — the web app binds "allsky" and "dome" to
        # the views of those names.
        "cameras": {},
        # escape hatch: go2rtc has no Homebrew formula and on Windows it lands
        # wherever the operator put it. Empty means "look on PATH".
        "go2rtc_bin": "",
    }

    #: camera sources carry rtsp://user:pass@… and get_status() feeds the
    #: unauthenticated WS gateway. See Manager.get_status.
    __config_private__ = ("cameras",)

    def __init__(self):
        ChimeraObject.__init__(self)
        self._proc: Go2rtcProcess | None = None
        self._binary: str | None = None
        self._yaml: str | None = None
        self._live: set[str] = set()
        self._backoff = BACKOFF_MIN
        self._retry_at = 0.0
        # 2 Hz is the ChimeraObject default and too fast for this: control()
        # makes a blocking HTTP call, and a wedged relay would trip the "control
        # loop took more than…" warning twice a second. Dome uses 1/4 Hz for the
        # same reason.
        self.set_hz(1 / 2.0)

    # -- lifecycle ---------------------------------------------------------

    def __start__(self):
        if self["public_host"] == "default":
            self["public_host"] = self.__bus__.url.host
        if int(self["rtsp_port"]) == 0:
            # resolved once, here, so the generated YAML names a real port and
            # a restart reuses it rather than drifting to a new one each tick
            self["rtsp_port"] = free_port()

        self._yaml = generate_config(
            cameras=dict(self["cameras"]),
            video_host=self["video_host"],
            video_port=int(self["video_port"]),
            rtsp_port=int(self["rtsp_port"]),
            webrtc=bool(self["webrtc"]),
            webrtc_port=int(self["webrtc_port"]),
            public_host=self["public_host"],
        )

        try:
            self._binary = resolve_binary(self["go2rtc_bin"] or None)
        except Go2rtcNotFoundException as error:
            # deliberately not fatal: an observatory must still open when the
            # monitoring relay is missing. Loud, actionable, and retried by
            # control() — the science stream is unaffected.
            self.log.error(str(error))
            return True

        self._spawn()
        return True

    def _spawn(self) -> bool:
        """Start the child and wait for its API. False if it did not come up."""
        assert self._binary is not None and self._yaml is not None
        proc = Go2rtcProcess(self._binary, self._yaml, int(self["video_port"]))
        try:
            proc.start()
        except Exception as error:
            # a busy 1984 and a binary that dies on its own config look the
            # same from here, and both are the operator's to fix
            self.log.error(f"go2rtc failed to start: {error}")
            proc.stop()
            return False

        self._proc = proc
        self._backoff = BACKOFF_MIN
        self.log.info(
            f"go2rtc {self._binary} serving {len(self['cameras'])} camera(s); "
            f"config at {proc.config_path}; "
            f"WebUI http://{self['public_host']}:{self['video_port']}/"
        )
        self._refresh_liveness()
        return True

    def __stop__(self):
        if self._proc is not None:
            self._proc.stop()
            self._proc = None
        self._live = set()
        return True

    # -- supervision -------------------------------------------------------

    def control(self):
        """The supervisor tick: is the child alive, and are the cameras?"""
        if self._binary is None:
            return True  # no binary: nothing to supervise, stay looping quietly

        if self._proc is None or not self._proc.is_alive():
            now = time.monotonic()
            if now < self._retry_at:
                return True
            if self._proc is not None:
                self.log.warning(
                    f"go2rtc exited with code {self._proc.returncode()}; restarting"
                )
                self._proc.stop()
                self._proc = None
                self._drop_liveness()
            if not self._spawn():
                self._retry_at = now + self._backoff
                self._backoff = min(self._backoff * 2, BACKOFF_MAX)
            return True

        self._refresh_liveness()
        return True

    def is_relaying(self):
        """True while the go2rtc child is up. The spawn and every restart are
        asynchronous, so tests and health checks need the answer — the same
        reason Chz1Streamer exposes is_streaming()."""
        return self._proc is not None and self._proc.is_alive()

    def _refresh_liveness(self) -> None:
        """Which streams the relay will serve. Published on the edge, not per poll.

        Measured against reality rather than assumed: /api/streams answers
        {name: {producers: [{url}], consumers: null}} for *configured* sources,
        whether or not the camera has ever been reached — go2rtc dials lazily,
        on the first consumer. So a non-empty `producers` says nothing about the
        camera, and treating it as liveness would mark every feed online forever
        and quietly defeat the fallback.

        What membership does tell us, truthfully: the relay is up and it
        accepted this source. A name we configured that is missing here is a
        source string go2rtc rejected — which is worth surfacing, and is the
        common typo.

        Whether the camera itself answers is only knowable by dialling it, and
        that is the browser's job: VideoTile shows "connecting" until the first
        frame. Probing every camera on every tick would hold a connection open
        to each of them all night to learn something the viewer learns for free.
        """
        if self._proc is None:
            return
        state = self._proc.probe()
        if state is None:
            self._drop_liveness()
            return

        live = {name for name in self["cameras"] if name in state}
        if live != self._live:
            self._live = live
            self.streams_changed()

    def _drop_liveness(self) -> None:
        if self._live:
            self._live = set()
            self.streams_changed()

    # -- the catalogue -----------------------------------------------------

    def stream_info(self):
        """One descriptor per configured camera — see Streamer.

        Endpoint keys are protocol names, not go2rtc's: swapping the relay for
        MediaMTX would change these URLs and nothing else in the system.
        """
        host = self["public_host"]
        api = f"http://{host}:{int(self['video_port'])}"
        descriptors = []

        for name in self["cameras"]:
            endpoints = {
                # fMP4 over one WebSocket: ~0.5-1 s, no ICE, survives any proxy
                # that forwards upgrades. The right default for a dashboard.
                "ws": f"ws://{host}:{int(self['video_port'])}/api/ws?src={name}",
                # 2-5 s, and the only one Safari plays with no JavaScript
                "hls": f"{api}/api/stream.m3u8?src={name}",
                # no codec, no player, unkillable — and the honest fallback when
                # a camera's H.264 is too noisy at night to encode sanely
                "mjpeg": f"{api}/api/stream.mjpeg?src={name}",
                # the poster for every tile
                "snapshot": f"{api}/api/frame.jpeg?src={name}",
            }
            if self["webrtc"]:
                # ~150-300 ms on a LAN, H.264 passed through untouched. WHEP
                # rather than go2rtc's native signalling: still an expired
                # Internet-Draft, but the one MediaMTX, LiveKit and Cloudflare
                # all speak.
                endpoints["whep"] = f"{api}/api/webrtc?src={name}"

            descriptors.append(
                {
                    "id": name,
                    "label": name.replace("-", " ").replace("_", " ").title(),
                    "kind": StreamKind.VIDEO.value,
                    "online": name in self._live,
                    "endpoints": endpoints,
                }
            )

        return descriptors
