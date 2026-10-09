"""get_status() must not hand out secrets.

It is what the WS gateway's list() and describe() project to any browser that
connects, and there is no auth in v1 — so a config key holding a camera
password or an API token has to be opt-out-able by name.
"""

from chimera.core.chimeraobject import ChimeraObject


class Plain(ChimeraObject):
    __config__ = {"device": "/dev/ttyS0"}


class Secretive(ChimeraObject):
    """A config with a credential in it, like a monitoring-camera list."""

    __config__ = {
        "device": "/dev/ttyS0",
        "cameras": "rtsp://admin:hunter2@192.168.0.247/Streaming/channels/101",
    }
    __config_private__ = ("cameras",)


def _entry(manager, path):
    return next(o for o in manager.get_status()["objects"] if o["path"] == path)


class TestConfigRedaction:
    def test_private_key_is_redacted(self, manager):
        assert manager.add_class(Secretive, "cams")

        config = _entry(manager, "/Secretive/cams")["config"]

        assert config["cameras"] == "***"
        # the key survives: a browser should see that it is set, not what to
        assert "cameras" in config
        # and no other key is touched
        assert config["device"] == "/dev/ttyS0"

    def test_the_secret_is_nowhere_in_the_payload(self, manager):
        assert manager.add_class(Secretive, "cams")

        # belt and braces — the whole blob, not just the one key we redacted
        assert "hunter2" not in str(manager.get_status())

    def test_objects_without_the_marker_are_untouched(self, manager):
        assert manager.add_class(Plain, "plain")

        assert _entry(manager, "/Plain/plain")["config"] == {"device": "/dev/ttyS0"}
