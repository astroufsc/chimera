"""End-to-end over loopback: a FakeCamera exposure leaves the streamer as a CHZ1 frame.

The whole chain is real — camera writes the FITS, the bus delivers readout_complete, the
controller's callback hops to the core's loop, the encoder runs — and the assertion is on
the wire bytes, because the wire is the contract: magic, JSON header, and a payload whose
bands invert back to the pixels the camera wrote.
"""

import json
import random

import numpy as np
import pytest
from astropy.io import fits
from chz1 import pedestal
from websockets.sync.client import connect

from chimera.controllers.chz1streamer import Chz1Streamer
from chimera.instruments.fakecamera import FakeCamera


@pytest.fixture
def system(manager, wait_for, tmp_path):
    port = random.randint(20000, 60000)
    manager.add_class(FakeCamera, "fake")
    manager.add_class(Chz1Streamer, "fake", {"ws_host": "127.0.0.1", "ws_port": port})
    # the subscription happens on the control-loop tick, not in __start__ —
    # the server's bus only dispatches after every __start__ has run
    streamer = manager.get_proxy("/Chz1Streamer/0")
    assert wait_for(lambda: streamer.is_streaming(), 10)
    yield manager.get_proxy("/Camera/0"), port, tmp_path


def test_expose_streams_a_chz1_frame(system):
    camera, port, tmp_path = system
    filename = tmp_path / "frame.fits"

    # connect first: the streamer skips the encode entirely when nobody is watching
    with connect(f"ws://127.0.0.1:{port}", open_timeout=10) as ws:
        urls = camera.expose(exptime=0.1, frames=1, filename=str(filename))
        assert len(urls) == 1

        message = ws.recv(timeout=30)
        assert isinstance(message, bytes)

        header, payload = pedestal.parse_message(message)
        assert header["seq"] == 1
        assert header["npix"] == header["w"] * header["h"]
        assert header["comp_bytes"] == len(payload)
        assert "zscale" in header["stats"]["limits"]

        # the payload inverts to exactly the pixels the camera wrote (mod the
        # streamer's clip of FakeCamera's float32 into the uint16 container)
        with fits.open(filename) as hdus:
            written = np.clip(np.rint(hdus[0].data), 0, 65535).astype(np.uint16)
        buf = pedestal.decompress_bands(payload, header)
        decoded = pedestal.filter_inverse(buf, header["w"], header["h"])
        assert decoded.shape == written.shape
        np.testing.assert_array_equal(decoded, written)

        # return the credit, as a well-behaved viewer would
        ws.send(json.dumps({"type": "ack", "seq": header["seq"]}))
