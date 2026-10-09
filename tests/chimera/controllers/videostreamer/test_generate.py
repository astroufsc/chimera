"""The generator, as what it is: config in, YAML out.

This is the part most likely to be quietly wrong. A relay that starts happily
with the wrong listen address looks exactly like one that started right, until
a browser on another host tries to dial it — which is a bug you find at the
telescope, at night, from a phone.
"""

import pathlib

import pytest
import yaml

from chimera.controllers.videostreamer.core import (
    Go2rtcNotFoundException,
    free_port,
    generate_config,
    resolve_binary,
)

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "go2rtc-proven.yaml"


@pytest.fixture
def proven():
    """The camera list from the config proved against real hardware."""
    return yaml.safe_load(FIXTURE.read_text())["streams"]


class TestSources:
    def test_proven_sources_round_trip_untouched(self, proven):
        """Every source string survives generation byte-for-byte.

        The source is the one field that stays go2rtc-shaped, because it is
        where the per-site knowledge lives. Rewriting it would be a translation
        layer with nothing to translate — so it must not be rewritten.
        """
        rendered = yaml.safe_load(generate_config(cameras=proven))

        assert rendered["streams"] == proven

    def test_the_rtsp_form_carries_no_transcode_suffix(self, proven):
        """An IP camera's H.264 comes off its ASIC; asking ffmpeg to re-encode
        it is the single biggest CPU sink in deployments like this."""
        for name, src in proven.items():
            if src.startswith("rtsp://"):
                assert "#video=" not in src, name

    def test_no_cameras_is_valid(self):
        rendered = yaml.safe_load(generate_config(cameras={}))

        assert rendered["streams"] == {}


class TestListenAddresses:
    def test_binds_where_told(self):
        rendered = yaml.safe_load(
            generate_config(
                cameras={}, video_host="127.0.0.1", video_port=9999, rtsp_port=9998
            )
        )

        assert rendered["api"]["listen"] == "127.0.0.1:9999"
        assert rendered["rtsp"]["listen"] == "127.0.0.1:9998"

    def test_webrtc_advertises_the_public_host_not_the_bind_host(self):
        """ICE candidates name an address the *browser* must reach.

        This is the bug that only shows up from a second machine: bind 0.0.0.0,
        advertise 0.0.0.0, and WebRTC negotiates against an address nothing can
        route to. Local testing never catches it.
        """
        rendered = yaml.safe_load(
            generate_config(
                cameras={},
                video_host="0.0.0.0",
                webrtc_port=8555,
                public_host="observatory.lna.br",
            )
        )

        assert rendered["webrtc"]["listen"] == "0.0.0.0:8555"
        assert rendered["webrtc"]["candidates"] == ["observatory.lna.br:8555"]
        assert "0.0.0.0" not in rendered["webrtc"]["candidates"][0]

    def test_the_api_accepts_cross_origin_upgrades(self):
        """Without api.origin, go2rtc answers 403 to the WebSocket upgrade and
        every feed is black.

        Measured against the real binary: a curl upgrade carrying
        Origin: http://localhost:5199 got 403 Forbidden, and 101 Switching
        Protocols once origin was set. The web app is *always* a different
        origin from the relay — the app is on a dev server or a static host,
        the relay is on 1984 — so this is not an edge case, it is every case.
        """
        rendered = yaml.safe_load(generate_config(cameras={}))

        assert rendered["api"]["origin"] == "*"

    def test_webrtc_off_emits_no_webrtc_block(self):
        rendered = yaml.safe_load(generate_config(cameras={}, webrtc=False))

        assert "webrtc" not in rendered

    def test_nothing_go2rtc_shaped_leaks_into_the_surface(self):
        """We own go2rtc, so nobody configures go2rtc. Codec templates, ICE
        servers, local_auth and base_path are generated or absent — never
        surfaced as chimera config."""
        rendered = yaml.safe_load(generate_config(cameras={}))

        assert set(rendered) <= {"api", "rtsp", "webrtc", "streams"}


class TestFreePort:
    """go2rtc's RTSP listener is internal plumbing, and a fixed 8554 breaks it.

    Every `ffmpeg:` source publishes into that listener. When it cannot bind —
    which happens the moment any other go2rtc is running, i.e. whenever someone
    is actually working on cameras — go2rtc logs "rtsp module disabled" and
    serves nothing from those sources, while its HTTP API answers normally and
    our start handshake reports a healthy relay.
    """

    def test_a_free_port_is_actually_free(self):
        import socket

        port = free_port()

        with socket.socket() as s:
            s.bind(("127.0.0.1", port))  # must not raise

    def test_two_calls_do_not_collide(self):
        assert free_port() != free_port()

    def test_the_generator_takes_a_concrete_port(self):
        """Resolution happens in the controller, so generate_config stays pure
        — config in, YAML out, no sockets."""
        rendered = yaml.safe_load(generate_config(cameras={}, rtsp_port=12345))

        assert rendered["rtsp"]["listen"].endswith(":12345")


class TestBinaryResolution:
    def test_a_bad_explicit_path_says_so(self, tmp_path):
        missing = str(tmp_path / "nope")

        with pytest.raises(Go2rtcNotFoundException, match="not an executable file"):
            resolve_binary(missing)

    def test_a_non_executable_file_is_not_the_binary(self, tmp_path):
        plain = tmp_path / "go2rtc"
        plain.write_text("not a binary")

        with pytest.raises(Go2rtcNotFoundException):
            resolve_binary(str(plain))

    def test_an_executable_is_taken_at_its_word(self, tmp_path):
        fake = tmp_path / "go2rtc"
        fake.write_text("#!/bin/sh\n")
        fake.chmod(0o755)

        assert resolve_binary(str(fake)) == str(fake)

    def test_the_missing_message_is_actionable(self, monkeypatch):
        """Not a traceback: it has to say where to get it and what happens
        meanwhile, because the person reading it is deploying, not debugging."""
        monkeypatch.setattr("shutil.which", lambda _: None)

        with pytest.raises(Go2rtcNotFoundException) as excinfo:
            resolve_binary(None)

        message = str(excinfo.value)
        assert "releases" in message
        assert "go2rtc_bin" in message
