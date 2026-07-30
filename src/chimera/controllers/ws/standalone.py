# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""chimera-ws: the WS gateway as a standalone process.

Joins the chimera server as a bus peer (own bus on an ephemeral port, same
pattern as the client CLIs) and serves WebSocket clients. Use this to run the
web gateway on another machine or restart it independently of the server.

The bus is symmetric: the server dials back to deliver responses and events,
so --bus-host must be an address the server can reach (auto-detected from the
route to the server by default).
"""

import argparse
import logging
import os
import random
import signal
import socket
import sys
import threading

import chimera.core.log
from chimera.controllers.ws.gateway import GatewayCore
from chimera.core.bus import Bus
from chimera.core.chimera_config import ChimeraConfig
from chimera.core.constants import (
    CHIMERA_CONFIG_DEFAULT_FILENAME,
    MANAGER_LOCATION,
)
from chimera.core.url import create_url
from chimera.core.version import chimera_version

log = logging.getLogger(__name__)


def _default_bus_host(server_host: str, server_port: int) -> str:
    """The local address used to reach the server: a connected UDP socket
    picks the right outgoing interface without sending a packet."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect((server_host, server_port))
            return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="chimera-ws",
        description="WebSocket gateway to a running chimera server",
    )
    parser.add_argument("--version", action="version", version=chimera_version)

    server = parser.add_argument_group("chimera server")
    server.add_argument(
        "--config",
        dest="config_file",
        default=CHIMERA_CONFIG_DEFAULT_FILENAME,
        metavar="FILE",
        help="chimera configuration file to read the server host/port from",
    )
    server.add_argument(
        "-H", "--host", help="chimera server host (overrides the config file)"
    )
    server.add_argument(
        "-P",
        "--port",
        type=int,
        help="chimera server port (overrides the config file)",
    )

    bus = parser.add_argument_group("gateway bus")
    bus.add_argument(
        "--bus-host",
        help="address this gateway's bus binds on; MUST be reachable from the "
        "server (default: the local address of the route to the server)",
    )
    bus.add_argument(
        "--bus-port",
        type=int,
        default=0,
        help="port this gateway's bus binds on (default: random)",
    )

    websocket = parser.add_argument_group("websocket server")
    websocket.add_argument("--ws-host", default="0.0.0.0")
    websocket.add_argument("--ws-port", type=int, default=7667)
    websocket.add_argument(
        "--max-calls",
        type=int,
        default=64,
        help="max concurrent in-flight bus calls",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0)
    return parser.parse_args(argv)


def main() -> int:
    options = parse_args()

    if options.verbose == 0:
        chimera.core.log.set_console_level(logging.WARNING)
    elif options.verbose == 1:
        chimera.core.log.set_console_level(logging.INFO)
    else:
        chimera.core.log.set_console_level(logging.DEBUG)

    server_host, server_port = options.host, options.port
    if server_host is None or server_port is None:
        try:
            config = ChimeraConfig.from_file(options.config_file)
            server_host = server_host or config.host
            server_port = server_port or config.port
        except OSError as error:
            log.error(f"cannot read configuration file: {error} (use -H/-P)")
            return 1

    bus_host = options.bus_host or _default_bus_host(server_host, server_port)
    bus_port = options.bus_port or random.randint(10000, 60000)

    bus = Bus(f"tcp://{bus_host}:{bus_port}")
    bus_thread = threading.Thread(
        target=bus.run_forever, name="chimera-ws-bus", daemon=True
    )
    bus_thread.start()
    if not bus._bus_started.wait(5):
        log.error("bus did not start")
        return 1

    core = GatewayCore(
        bus=bus,
        gateway_url=create_url(bus=bus.url.bus, cls="WsGateway", name="ws").url,
        manager_url=f"tcp://{server_host}:{server_port}{MANAGER_LOCATION}",
        ws_host=options.ws_host,
        ws_port=options.ws_port,
        max_calls=options.max_calls,
        standalone=True,
    )
    try:
        core.start()
    except RuntimeError:
        log.exception("gateway failed to start")
        bus.shutdown()
        bus_thread.join(timeout=10)
        return 1

    log.info(
        f"chimera-ws: serving ws://{options.ws_host}:{options.ws_port} "
        f"for chimera server {server_host}:{server_port} "
        f"(gateway bus {bus_host}:{bus_port})"
    )

    shutdown_requested = threading.Event()

    def shutdown():
        # gateway first (needs the bus to unsubscribe), bus last
        core.stop()
        bus.shutdown()

    def on_sigint(signum, frame):
        # no logging in a signal handler; second ctrl-c force-quits
        if shutdown_requested.is_set():
            os.write(2, b"ctrl-c again: forcing exit\n")
            os._exit(130)
        shutdown_requested.set()
        threading.Thread(target=shutdown, name="chimera-ws-shutdown").start()

    signal.signal(signal.SIGINT, on_sigint)

    bus_thread.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
