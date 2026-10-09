"""A stand-in for go2rtc.

Supervision is the genuinely new thing here — no chimera controller had ever
owned a child process — so it needs testing against a real child, not a mock.
This is the smallest program that behaves like go2rtc from the supervisor's
point of view: it reads -config, binds the api.listen port, and answers
/api/streams. What it does not do is speak RTSP or H.264, which is exactly the
part we do not write and therefore do not test.
"""

import random
import socket
import textwrap

import pytest

FAKE_GO2RTC = """#!/usr/bin/env python3
import json, os, sys, re
from http.server import BaseHTTPRequestHandler, HTTPServer

config = sys.argv[sys.argv.index("-config") + 1]
text = open(config).read()

# one line per spawn, so a supervision test can prove a *new* child replaced
# the old one rather than the old one having never died
if PIDS:
    with open(PIDS, "a") as fp:
        fp.write(f"{os.getpid()}\\n")

# deliberately not yaml.safe_load: the stand-in must not need chimera's deps
port = int(re.search(r"listen: '?[^:'\\n]*:(\\d+)'?", text).group(1))
# only the streams block — api/webrtc have indented keys of their own
block = text.split("streams:", 1)[1] if "streams:" in text else ""
names = re.findall(r"^  ([^\\s:]+):", block, re.M)

STATE = {n: {"producers": [{"url": "fake"}], "consumers": []} for n in names}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/api/streams"):
            self.send_error(404)
            return
        body = json.dumps(STATE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""


def _write(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(textwrap.dedent(source))
    path.chmod(0o755)
    return str(path)


def _fake(tmp_path, pids=None):
    header = f"PIDS = {str(pids)!r}\n" if pids else "PIDS = None\n"
    return _write(
        tmp_path,
        "go2rtc",
        FAKE_GO2RTC.replace("import json", header + "import json", 1),
    )


@pytest.fixture
def fake_go2rtc(tmp_path):
    """A binary that comes up and serves /api/streams."""
    return _fake(tmp_path)


@pytest.fixture
def fake_go2rtc_logging_pids(tmp_path):
    """The same, but recording each spawn's pid. Returns (binary, pid_file)."""
    pids = tmp_path / "pids"
    return _fake(tmp_path, pids=pids), pids


@pytest.fixture
def talkative_go2rtc(tmp_path):
    """Serves /api/streams and also says something on stdout and stderr, tagged
    the way go2rtc tags its own lines, so the log pump has real output to
    forward — including one ERR that must be raised to warning."""
    chatty = FAKE_GO2RTC.replace(
        'HTTPServer(("127.0.0.1", port), Handler).serve_forever()',
        'print("13:00:00.000 INF hello from the relay", flush=True)\n'
        'print("13:00:00.001 ERR something went wrong", file=sys.stderr, flush=True)\n'
        'HTTPServer(("127.0.0.1", port), Handler).serve_forever()',
        1,
    )
    # same shebang-preserving insertion _fake uses
    return _write(
        tmp_path, "go2rtc", chatty.replace("import json", "PIDS = None\nimport json", 1)
    )


@pytest.fixture
def dying_go2rtc(tmp_path):
    """A binary that exits at once, the way a bad config makes the real one."""
    return _write(tmp_path, "go2rtc-dies", "#!/bin/sh\nexit 3\n")


@pytest.fixture
def mute_go2rtc(tmp_path):
    """A binary that runs forever and never binds — the wedged case."""
    return _write(tmp_path, "go2rtc-mute", "#!/bin/sh\nsleep 300\n")


@pytest.fixture
def free_port():
    """A port nothing is listening on, taken the way the other suites take one."""
    for _ in range(50):
        port = random.randint(20000, 60000)
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free port found")
