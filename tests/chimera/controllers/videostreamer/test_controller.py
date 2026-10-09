"""The controller under a real manager: descriptors, restarts, and the day
go2rtc is not installed.

The last one is not an edge case. go2rtc is a binary on PATH rather than a
Python dependency — which is what keeps `uv sync` and the wheel clean — so
"it is missing" is the normal state of every machine until someone installs it,
and an observatory has to open anyway.
"""

import os
import signal
import time

import pytest

from chimera.controllers.videostreamer import VideoStreamer

CAMERAS = {
    "dome": "rtsp://admin:hunter2@192.168.0.50:554/Streaming/channels/101",
    "allsky": "ffmpeg:device?video=0#video=h264",
}


@pytest.fixture
def relay(manager, wait_for, fake_go2rtc, free_port):
    manager.add_class(
        VideoStreamer,
        "site",
        {
            "go2rtc_bin": fake_go2rtc,
            "video_host": "127.0.0.1",
            "video_port": free_port,
            "public_host": "obs.example",
            "cameras": CAMERAS,
        },
    )
    proxy = manager.get_proxy("/VideoStreamer/site")
    assert wait_for(lambda: proxy.is_relaying(), 10)
    return proxy


class TestDescriptors:
    def test_one_descriptor_per_camera(self, relay):
        descriptors = relay.stream_info()

        assert {d["id"] for d in descriptors} == set(CAMERAS)
        assert all(d["kind"] == "video" for d in descriptors)

    def test_endpoints_are_protocol_named_not_vendor_named(self, relay):
        """Swapping go2rtc for MediaMTX must change URLs and nothing else, so
        the keys are what the wire speaks, not what the relay is called."""
        endpoints = relay.stream_info()[0]["endpoints"]

        assert set(endpoints) == {"ws", "hls", "mjpeg", "snapshot", "whep"}
        assert not any("go2rtc" in key for key in endpoints)

    def test_every_url_is_dialable_from_elsewhere(self, relay):
        """0.0.0.0 is where we bind. A descriptor carrying it is a descriptor
        that works on localhost and nowhere else."""
        for descriptor in relay.stream_info():
            for url in descriptor["endpoints"].values():
                assert "0.0.0.0" not in url
                assert "obs.example" in url

    def test_online_follows_the_relay(self, relay):
        assert all(d["online"] for d in relay.stream_info())

    def test_a_source_go2rtc_rejected_reads_offline(
        self, manager, wait_for, fake_go2rtc, free_port
    ):
        """online means "the relay accepted this source and is up".

        Measured against the real go2rtc: /api/streams lists configured sources
        whether or not the camera was ever reached, because it dials lazily. So
        a name missing from the answer is a source string it rejected — the
        common typo — and that is the one thing this field can honestly report.
        """
        manager.add_class(
            VideoStreamer,
            "site",
            {
                "go2rtc_bin": fake_go2rtc,
                "video_host": "127.0.0.1",
                "video_port": free_port,
                # the stand-in registers only what it finds in the streams
                # block; "ghost" is configured but never reaches go2rtc
                "cameras": {"dome": "rtsp://10.0.0.1/s"},
            },
        )
        proxy = manager.get_proxy("/VideoStreamer/site")
        assert wait_for(lambda: proxy.is_relaying(), 10)

        proxy["cameras"] = {"dome": "rtsp://10.0.0.1/s", "ghost": "rtsp://nope/"}

        by_id = {d["id"]: d for d in proxy.stream_info()}
        assert by_id["dome"]["online"] is True
        assert by_id["ghost"]["online"] is False


class TestSecrets:
    def test_camera_sources_never_reach_the_catalogue(self, relay, manager):
        """The sources carry rtsp://user:pass@… and get_status() feeds an
        unauthenticated gateway."""
        entry = next(
            o
            for o in manager.get_status()["objects"]
            if o["path"] == "/VideoStreamer/site"
        )

        assert entry["config"]["cameras"] == "***"
        assert "hunter2" not in str(manager.get_status())

    def test_nor_do_they_reach_the_descriptors(self, relay):
        assert "hunter2" not in str(relay.stream_info())


class TestSupervision:
    def test_a_dead_child_is_replaced(
        self, manager, wait_for, fake_go2rtc_logging_pids, free_port
    ):
        binary, pid_file = fake_go2rtc_logging_pids
        manager.add_class(
            VideoStreamer,
            "site",
            {
                "go2rtc_bin": binary,
                "video_host": "127.0.0.1",
                "video_port": free_port,
                "cameras": {"dome": "rtsp://10.0.0.1/s"},
            },
        )
        proxy = manager.get_proxy("/VideoStreamer/site")
        assert wait_for(lambda: proxy.is_relaying(), 10)
        assert wait_for(lambda: pid_file.exists(), 10)

        first = int(pid_file.read_text().split()[0])
        os.kill(first, signal.SIGKILL)

        # control() runs at 1/2 Hz, so give it several ticks. The pid lands
        # before the replacement has bound its port — start() waits for the API
        # — so the relay flag has to be waited on separately, not asserted.
        assert wait_for(lambda: len(pid_file.read_text().split()) >= 2, 20)
        second = int(pid_file.read_text().split()[1])
        assert second != first

        assert wait_for(lambda: proxy.is_relaying(), 20)

    def test_shutdown_leaves_no_orphan(
        self, manager, wait_for, fake_go2rtc_logging_pids, free_port
    ):
        binary, pid_file = fake_go2rtc_logging_pids
        manager.add_class(
            VideoStreamer,
            "site",
            {
                "go2rtc_bin": binary,
                "video_host": "127.0.0.1",
                "video_port": free_port,
                "cameras": {"dome": "rtsp://10.0.0.1/s"},
            },
        )
        proxy = manager.get_proxy("/VideoStreamer/site")
        assert wait_for(lambda: proxy.is_relaying(), 10)
        assert wait_for(lambda: pid_file.exists(), 10)
        pid = int(pid_file.read_text().split()[0])

        manager.remove("/VideoStreamer/site")

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except OSError:
                return  # reaped
            time.sleep(0.1)
        pytest.fail(f"go2rtc {pid} outlived its controller")


class TestMissingBinary:
    """The binary is absent — one clear error, and everything else still runs."""

    @pytest.fixture
    def offline(self, manager, monkeypatch, tmp_path):
        monkeypatch.setattr("shutil.which", lambda _: None)
        manager.add_class(VideoStreamer, "site", {"cameras": CAMERAS, "go2rtc_bin": ""})
        return manager.get_proxy("/VideoStreamer/site")

    def test_the_controller_still_starts(self, offline):
        assert offline.is_relaying() is False

    def test_the_catalogue_still_answers_with_everything_offline(self, offline):
        descriptors = offline.stream_info()

        assert {d["id"] for d in descriptors} == set(CAMERAS)
        assert not any(d["online"] for d in descriptors)

    def test_the_rest_of_chimera_is_unaffected(self, offline, manager):
        """Especially the science stream — a missing monitoring relay must not
        cost anyone their data."""
        from chimera.instruments.fakecamera import FakeCamera

        assert manager.add_class(FakeCamera, "fake")
        assert manager.get_proxy("/Camera/0") is not None
