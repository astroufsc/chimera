# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.event import event
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class StreamKind(Enum):
    """What is on the wire, which is also how the browser dispatches.

    PIXELS is CHZ1: one plane of uint16 ADU, intra-only, the value *is* the
    measurement — it goes to @astro-ph/viewer. VIDEO is a camera codec
    (H.264 and friends): three planes, 8-bit, perceptual and inter-frame
    predicted — it goes to a <video> element. There is no third kind, and
    nothing converts between these two: see docs/plans/streaming/.
    """

    PIXELS = "pixels"
    VIDEO = "video"


class Streamer(Interface):
    """What streams exist, and where does a browser dial them?

    A catalogue, not a codec. Implementors share no runtime machinery — the
    science path encodes CHZ1 in-process, the monitoring path supervises a
    relay that dials cameras itself — so this interface abstracts over the
    only thing they have in common: a name, a kind, and some URLs.

    Deliberately no ``__config__``. MetaObject merges config down the MRO, so
    a key declared here would silently appear on every implementor and in
    every ``list()`` response; this interface describes streams rather than
    configuring them.
    """

    def stream_info(self) -> list[dict]:
        """One descriptor per stream this object serves.

        A list even when there is exactly one, so that callers never special
        case a single-stream publisher::

            {"id": "dome",                    # stable, unique within the bus
             "label": "Dome",                 # for humans
             "kind": "video",                 # StreamKind value
             "online": True,                  # will the server serve it now?
             "endpoints": {"whep": "http://obs:1984/api/webrtc?src=dome",
                           "mjpeg": "http://obs:1984/api/stream.mjpeg?src=dome",
                           ...}}

        Endpoint keys are *protocol* names — whep, ws, hls, mjpeg, snapshot,
        chz1 — never the relay vendor's names, so swapping the relay changes
        URLs and nothing else.

        ``online`` is a statement about the *server*, not the camera: this end
        is up and will serve the stream if asked. Whether the far end answers
        is only knowable by dialling it, which is the client's job — an
        implementor must not hold a connection open to every source all night
        to answer a field.

        Every URL is absolute and dialable from another host: the server
        resolves its own public address (the ``"default"`` convention, as
        ImageServer does) and the browser never assembles one. A bind address
        such as 0.0.0.0 must never appear here.

        @return: descriptors, possibly empty
        @rtype: list of dict
        """

    @event
    def streams_changed(self) -> None:
        """A stream came up or went down; re-read stream_info().

        Liveness only — the set of configured streams does not change at
        runtime. Raised on the edge, not on every poll.
        """
