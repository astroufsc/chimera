"""The streaming core: one thread, one asyncio loop, one WebSocket server.

The controller stays a thin lifecycle shim; everything that owns a resource lives here, in
the arrangement `controllers/ws/gateway.py` proved out: a dedicated thread runs
`asyncio.run`, `start()` blocks on a handshake so a bind failure surfaces as an exception
out of `__start__`, and `stop()` signals the loop with `call_soon_threadsafe` and joins.

Frames come in as bus-event URLs (`submit_threadsafe`, called from a bus handler-pool
thread) and go out as CHZ1 messages — the wire format is `chz1`'s `protocol.md`, the
encoder is `chz1.pedestal` (pinned byte-for-byte to that repo's fixtures), and the framing
rules are the reference server's:

- **BINARY out, TEXT in.** A frame is `bytes` so the browser sees a BINARY WS message; the
  client's `ack` and `config` messages are JSON text. (The WS gateway sends TEXT on
  purpose for the opposite reason — JSON as bytes surfaces as a Blob.)
- **Credit-based flow control.** Each session holds `inflight` credits; a send costs one,
  an `ack` returns one. A viewer that stalls stops consuming frames without stalling the
  camera or any other viewer.
- **Latest-frame-wins.** A camera pushes; there is no point queueing history. One shared
  latest message, a per-session cursor, and a session that missed three frames sends the
  newest, not the backlog.
- **The `accept` gate.** Binning and quantization stay off until a client names them in a
  `config` message — the rule that let the preview tier ship without bumping the `CHZ1`
  magic. Config is last-writer-wins across sessions, as in the reference server; the
  encode is shared, not per-client.

The FITS read and the encode run on a single-worker executor: `Encoder` holds a reusable
~2·npix buffer and is not thread-safe, and one worker serialises encodes without a lock
while `_drain` coalesces submissions so a burst of readouts encodes only the newest.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from astropy.io import fits
from chz1 import pedestal
from chz1.fits import read_wcs
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

log = logging.getLogger(__name__)

# Subsample stride for the display-limit statistics, from the reference server: coprime
# with common row lengths, and a ~3% sample is plenty for 16-bit percentiles.
STAT_STRIDE = 37


class _Session:
    """What the core knows about one connected viewer: its credit, nothing else."""

    def __init__(self, inflight: int):
        self.credit = asyncio.Semaphore(inflight)


class StreamerCore:
    def __init__(
        self,
        *,
        ws_host: str,
        ws_port: int,
        bands: int,
        level: int,
        tile_rows: int,
        dezero: bool,
        inflight: int,
    ):
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.bands = bands
        self.level = level
        self.tile_rows = tile_rows
        self.dezero = dezero
        self.inflight = inflight

        # preview tier, off until a client's config names it (the accept gate)
        self.accept: frozenset[str] = frozenset()
        self.bin = 1
        self.q = 0.0
        self.dither = True
        self.qseed = 0x5EED1234

        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._startup_error: BaseException | None = None
        self._stop_requested: asyncio.Event | None = None
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="chimera-chz1-encode"
        )

        self._sessions: set[_Session] = set()
        self._cond: asyncio.Condition | None = None
        self._pending: str | None = None
        self._encode_task: asyncio.Task | None = None
        self._latest: bytes | None = None
        self._latest_seq = 0
        self._seq = 0
        self._encoders: dict[tuple[int, int], pedestal.Encoder] = {}

    # -- lifecycle (the gateway.py pattern) ------------------------------------------------

    def start(self, timeout: float = 10.0) -> None:
        self._thread = threading.Thread(
            target=self._run, name="chimera-chz1-loop", daemon=True
        )
        self._thread.start()
        if not self._started.wait(timeout):
            raise RuntimeError("CHZ1 streamer did not start in time")
        if self._startup_error is not None:
            raise RuntimeError("CHZ1 streamer failed to start") from self._startup_error

    def stop(self) -> None:
        if self.loop is not None and self._stop_requested is not None:
            try:
                self.loop.call_soon_threadsafe(self._stop_requested.set)
            except RuntimeError:
                pass  # loop already closed
        if self._thread is not None:
            self._thread.join(timeout=10.0)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run(self) -> None:
        try:
            asyncio.run(self._main())
        except BaseException as error:  # startup failures (port in use, ...)
            self._startup_error = error
            self._started.set()
            log.exception("CHZ1 streamer loop died")

    async def _main(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._stop_requested = asyncio.Event()
        self._cond = asyncio.Condition()

        async with serve(self._handler, self.ws_host, self.ws_port):
            log.info(f"CHZ1 streamer listening on ws://{self.ws_host}:{self.ws_port}")
            self._started.set()
            await self._stop_requested.wait()

    # -- frames in -------------------------------------------------------------------------

    def submit_threadsafe(self, image_url: str) -> None:
        """Hand a readout's URL to the loop. Called from a bus handler-pool thread —
        never block here; the 64-slot pool is shared with every RPC on the bus."""
        loop = self.loop
        if loop is not None and not loop.is_closed():
            loop.call_soon_threadsafe(self._submit, image_url)

    def _submit(self, image_url: str) -> None:
        # loop thread. No viewers, no work: the subscription is standing, the encode is not.
        if not self._sessions:
            return
        self._pending = image_url
        if self._encode_task is None or self._encode_task.done():
            self._encode_task = asyncio.create_task(self._drain())

    async def _drain(self) -> None:
        assert self.loop is not None and self._cond is not None
        while self._pending is not None:
            url, self._pending = self._pending, None
            try:
                built = await self.loop.run_in_executor(
                    self._executor, self._build, url
                )
            except Exception:
                log.exception(f"encoding {url} failed")
                continue
            if built is None:
                continue
            message, seq = built
            self._latest, self._latest_seq = message, seq
            async with self._cond:
                self._cond.notify_all()

    # -- sessions --------------------------------------------------------------------------

    async def _handler(self, ws) -> None:
        session = _Session(self.inflight)
        self._sessions.add(session)
        sender = asyncio.create_task(self._sender(ws, session))
        try:
            async for message in ws:
                if isinstance(message, str):
                    self._handle_text(message, session)
        except ConnectionClosed:
            pass
        finally:
            self._sessions.discard(session)
            sender.cancel()
            try:
                await sender
            except (asyncio.CancelledError, ConnectionClosed):
                pass

    async def _sender(self, ws, session: _Session) -> None:
        assert self._cond is not None
        sent_seq = 0
        while True:
            # Credit first, then the newest frame at the moment we hold it — so a slow
            # viewer that finally acks gets the current sky, not the one it stalled on.
            await session.credit.acquire()
            async with self._cond:
                await self._cond.wait_for(lambda: self._latest_seq > sent_seq)
                message, sent_seq = self._latest, self._latest_seq
            assert message is not None
            await ws.send(message)  # bytes -> a BINARY frame, deliberately

    def _handle_text(self, message: str, session: _Session) -> None:
        try:
            m = json.loads(message)
        except ValueError:
            return
        kind = m.get("type")
        if kind == "ack":
            session.credit.release()
        elif kind == "config":
            # last-config-wins, as in the reference server. `inflight` sizes the credit
            # semaphore at connect time, so it applies to the next connection.
            if "inflight" in m:
                self.inflight = max(1, int(m["inflight"]))
            if "bands" in m:
                self.bands = max(1, int(m["bands"]))
            if "accept" in m:
                self.accept = frozenset(str(c) for c in (m["accept"] or []))
            if "bin" in m:
                self.bin = max(1, int(m["bin"]))
            if "q" in m:
                self.q = max(0.0, float(m["q"]))
            if "dither" in m:
                self.dither = bool(m["dither"])

    # -- the encode (single executor worker; nothing here touches the loop) -----------------

    def _build(self, image_url: str) -> tuple[bytes, int] | None:
        t0 = time.perf_counter()
        data, codec, wcs, obj, name, src_bytes = self._load(image_url)
        read_ms = (time.perf_counter() - t0) * 1e3

        src_h, src_w = data.shape
        sent, idx, wire = self._prepare(data)
        h, w = idx.shape
        enc = self._encoder(w, h)
        self._seq += 1
        seq = self._seq

        t0 = time.perf_counter()
        shift = enc.filter_forward(idx)
        filter_ms = (time.perf_counter() - t0) * 1e3
        t0 = time.perf_counter()
        blobs, layout = enc.compress_bands(self.bands)
        zstd_ms = (time.perf_counter() - t0) * 1e3

        t0 = time.perf_counter()
        stats = self._stats(sent)
        stats_ms = (time.perf_counter() - t0) * 1e3

        header: dict[str, Any] = {
            "seq": seq,
            "name": name,
            "w": w,
            "h": h,
            "tile_rows": enc.tile_rows,
            "shift": shift,
            "n_tiles": enc.n_tiles,
            "npix": enc.npix,
            "raw_bytes": 2 * enc.npix,
            "comp_bytes": sum(len(b) for b in blobs),
            "planes_off": enc.planes_off,
            "bands": pedestal.band_dicts(layout),
            "stats": stats,
            "probe": pedestal.probe_patch(sent),
            **(
                {"bin": wire["bin"], "src_w": src_w, "src_h": src_h}
                if wire["bin"] > 1
                else {}
            ),
            **({k: v for k, v in wire.items() if k != "bin"} if wire["qstep"] else {}),
            **({"wcs": self._scale_wcs(wcs, wire["bin"])} if wcs else {}),
            **({"object": obj} if obj else {}),
            "server": {
                "read_ms": round(read_ms, 2),
                "filter_ms": round(filter_ms, 2),
                "zstd_ms": round(zstd_ms, 2),
                "stats_ms": round(stats_ms, 2),
                "bands": len(layout),
                "level": self.level,
                "src_codec": codec,
                "src_bytes": src_bytes,
            },
        }
        return pedestal.build_message(header, blobs), seq

    def _encoder(self, w: int, h: int) -> pedestal.Encoder:
        key = (w, h)
        enc = self._encoders.get(key)
        if enc is None:
            enc = pedestal.Encoder(
                w, h, tile_rows=self.tile_rows, level=self.level, dezero=self.dezero
            )
            self._encoders[key] = enc
        return enc

    def _load(
        self, image_url: str
    ) -> tuple[np.ndarray, str, dict | None, str | None, str, int]:
        """Open the readout the event announced: the local path first (instruments and
        controllers share one process in the standard deployment), the ImageServer HTTP
        half when this streamer runs as a remote peer. Not `Image.from_url` — that
        returns None silently and exposes no pixels."""
        file_part, _, http_part = image_url.partition(",")
        name = file_part.rstrip("/").rsplit("/", 1)[-1] or "frame"
        if file_part.startswith("file://"):
            path = file_part[7:]
            if os.path.exists(path):
                return self._read(path, name, os.path.getsize(path))
        if http_part.startswith("http"):
            with urllib.request.urlopen(http_part, timeout=30) as response:
                payload = response.read()
            return self._read(io.BytesIO(payload), name, len(payload))
        raise ValueError(f"cannot open {image_url!r}")

    @staticmethod
    def _read(
        src: Any, name: str, src_bytes: int
    ) -> tuple[np.ndarray, str, dict | None, str | None, str, int]:
        with fits.open(src) as hdus:
            # walk the HDUs rather than taking [0]: RICE-compressed .fz files keep the
            # pixels in HDU 1 behind an empty primary
            for hdu in hdus:
                if hdu.data is None:
                    continue
                codec = getattr(hdu, "compression_type", None) or "none"
                data = hdu.data
                if data.ndim != 2:
                    raise ValueError(f"{name}: expected a 2D image, got {data.shape}")
                if data.dtype != np.uint16:
                    # Drivers write int16+BZERO, which astropy already unfolds, so
                    # this normally does nothing -- it is here for a file from
                    # somewhere else, or a driver that hands over floats. (Until
                    # 2026-08-22 FakeCamera was one, which is what this was written
                    # for.) Clip instead of cast: a stray negative or a >65535 float
                    # must saturate, not wrap.
                    data = np.clip(np.rint(data), 0, 65535).astype(np.uint16)
                data = np.ascontiguousarray(data)
                header = hdu.header
                return (
                    data,
                    codec,
                    read_wcs(header),
                    header.get("OBJECT"),
                    name,
                    src_bytes,
                )
        raise ValueError(f"{name}: no image HDU")

    # -- preview tier and statistics, ported from the reference server ----------------------

    def _prepare(self, data: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
        """Bin, measure the noise, quantize — each gated on the client's `accept`.

        Returns `(sent, indices, wire)`: `sent` is the frame the client should
        reconstruct (binned, before quantization — the probe patch and the display
        limits come from it, turning the probe read-back into an assertion of the error
        bound), `indices` is what the encoder filters, `wire` the header fields.
        """
        bin_factor = self.bin if "bin" in self.accept else 1
        q = self.q if "quant" in self.accept else 0.0

        binned, _ = pedestal.bin_forward(data, bin_factor)
        wire: dict[str, Any] = {"bin": bin_factor, "qstep": 0}
        if q <= 0:
            return binned, binned, wire

        sigma = pedestal.noise_sigma(binned)
        step = pedestal.step_for_q(sigma, q)
        if step <= 1:
            # a 1 ADU step is the identity — after bin 4 the noise is a quarter of what
            # it was, and a gentle q lands here routinely
            return binned, binned, wire

        quantizer = pedestal.Quantizer(step, seed=self.qseed, dither=self.dither)
        idx = quantizer.forward(binned)
        wire.update(quantizer.header_fields(sigma))
        return binned, idx, wire

    @staticmethod
    def _stats(data: np.ndarray) -> dict:
        """Every scale-limit option the client can pick, from one strided subsample —
        the bands are DS9's central percentiles, zscale is IRAF's via astropy."""
        sub = data.reshape(-1)[::STAT_STRIDE]
        hist = np.bincount(sub, minlength=65536)
        nz = np.flatnonzero(hist)
        cdf = np.cumsum(hist)
        total = int(cdf[-1])

        def band(pct: float) -> list[int]:
            tail = (100.0 - pct) / 200.0
            lo, hi = np.searchsorted(cdf, [tail * total, (1.0 - tail) * total])
            return [int(lo), int(hi)]

        limits = {
            "minmax": [int(nz[0]), int(nz[-1])],
            "99.5%": band(99.5),
            "99%": band(99.0),
            "95%": band(95.0),
            "zscale": StreamerCore._zscale(sub),
        }
        return {"min": int(nz[0]), "max": int(nz[-1]), "limits": limits}

    @staticmethod
    def _zscale(sub: np.ndarray) -> list[int]:
        from astropy.visualization import ZScaleInterval

        try:
            lo, hi = ZScaleInterval(n_samples=5000).get_limits(sub)
        except Exception:  # degenerate frames (all one value) make the line fit fail
            return [int(sub.min()), int(sub.max())]
        return [int(round(lo)), int(round(hi))]

    @staticmethod
    def _scale_wcs(wcs: dict | None, bin_factor: int) -> dict | None:
        """Rescale a CD-matrix WCS onto a binned grid: `crpix` converts through the
        pixel edge, `cd` simply scales. Skipping this mis-registers the sky silently."""
        if not wcs or bin_factor <= 1:
            return wcs
        out = dict(wcs)
        out["crpix"] = [(c - 0.5) / bin_factor + 0.5 for c in wcs["crpix"]]
        out["cd"] = [[v * bin_factor for v in row] for row in wcs["cd"]]
        return out
