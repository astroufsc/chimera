"""Chz1Streamer: every readout, pushed to browsers as a CHZ1 frame.

The WS gateway carries the bus — calls, events, JSON. Pixels do not fit through it
(`msgspec.json`, TEXT frames, and rightly so), and fetching the FITS back over HTTP makes
every viewer re-parse what the server already had in memory. This controller is the third
port: it subscribes to the camera's `readout_complete`, opens the file the event names,
encodes it once with `chz1.pedestal`, and pushes the result over its own WebSocket to any
number of viewers — `@astro-ph/viewer`'s worker connects, decodes in a pool, and paints.

Declare it in chimera.config next to the gateway:

    controller:
      - type: Chz1Streamer
        name: fake
        ws_port: 7668

The split mirrors WsGateway/GatewayCore: this class is only lifecycle and configuration,
`StreamerCore` owns the thread, the loop, the server and the encoder — which is also what
makes the core testable on a random port without a manager-registered controller.
"""

from chimera.controllers.chz1streamer.core import StreamerCore
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException
from chimera.interfaces.streamer import Streamer, StreamKind


class Chz1Streamer(ChimeraObject, Streamer):
    __config__ = {
        # the camera whose readouts are streamed; resolved by base class, so
        # /Camera/0 finds FakeCamera and real drivers alike
        "camera": "/Camera/0",
        "ws_host": "0.0.0.0",
        "ws_port": 7668,
        # what a browser dials, as opposed to what we bind: "default" resolves
        # to the bus host at __start__, the same convention ImageServer uses.
        # ws_host is 0.0.0.0 and must never reach a client.
        "public_host": "default",
        # CHZ1 encode parameters: 8 bands paint progressively, level 1 is the
        # measured speed/size knee, dezero strips constant-zero low bits (Ares-M)
        "bands": 8,
        "level": 1,
        "tile_rows": 32,
        "dezero": True,
        # frames a client may hold unacked before the streamer stops sending to it
        "inflight": 2,
    }

    def __init__(self):
        ChimeraObject.__init__(self)
        self._core: StreamerCore | None = None
        self._camera = None
        self._clbk = None

    def __start__(self):
        if self["public_host"] == "default":
            self["public_host"] = self.__bus__.url.host
        core = StreamerCore(
            ws_host=self["ws_host"],
            ws_port=self["ws_port"],
            bands=self["bands"],
            level=self["level"],
            tile_rows=self["tile_rows"],
            dezero=self["dezero"],
            inflight=self["inflight"],
        )
        core.start()  # raises out of __start__ if the port cannot be bound
        self._core = core
        return True

    def control(self):
        # The subscription cannot happen in __start__: the server starts its bus
        # dispatch loop only after every object's __start__ has run (chimera.py
        # calls run_forever last), so a self-ping cannot be answered yet — which
        # is why everything in this tree resolves proxies at use time. The
        # control loop runs on a pool thread instead: the first tick that finds
        # the camera subscribes and stops the loop, earlier ones just retry.
        if self._core is None:
            return False
        try:
            # NOTE: keep the callback reference — the bus matches unsubscribe by ==
            camera = self.get_proxy(self["camera"])
            self._clbk = self._on_readout_complete
            camera.readout_complete += self._clbk
            self._camera = camera
        except ChimeraException:
            return True  # bus not dispatching yet, or no camera yet
        self.log.info(f"streaming readouts of {self['camera']}")
        return False

    def stream_info(self):
        """The one CHZ1 stream this controller serves — see Streamer.

        Named after the camera rather than the controller: the id has to stay
        stable and unique once a second science camera exists, and it is the
        camera that a viewer is actually looking at.
        """
        camera = self["camera"].strip("/").replace("/", "-").lower()
        host, port = self["public_host"], int(self["ws_port"])
        return [
            {
                "id": camera,
                "label": self["camera"],
                "kind": StreamKind.PIXELS.value,
                "online": self._core is not None,
                "endpoints": {"chz1": f"ws://{host}:{port}/"},
            }
        ]

    def is_streaming(self):
        """True once the readout subscription is standing. The subscription is
        asynchronous (see control), so tests and health checks need the answer."""
        return self._clbk is not None

    def __stop__(self):
        if self._camera is not None and self._clbk is not None:
            try:
                self._camera.readout_complete -= self._clbk
            except Exception:
                pass  # the camera may already be gone at shutdown
            self._camera = None
            self._clbk = None
        if self._core is not None:
            self._core.stop()
            self._core = None
        return True

    def _on_readout_complete(self, image_url, status):
        # bus handler-pool thread (64 slots, shared with every RPC): guard and hop,
        # nothing else. The read and the encode happen on the core's own executor.
        core = self._core
        if core is None or not isinstance(image_url, str):
            return
        # local delivery hands us the CameraStatus enum, remote delivery its value
        if getattr(status, "value", status) != "OK":
            return
        core.submit_threadsafe(image_url)
