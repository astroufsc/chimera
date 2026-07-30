# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""The WS gateway as a chimera controller: declare it in chimera.config and
the manager runs it inside the server process.

    controller:
      type: WsGateway
      name: ws
      ws_port: 7667

This is the recommended deployment: the gateway shares the manager's bus, so
every call and event is delivered locally (no serialization, no peering, no
eviction — the standalone re-subscribe watchdog is unnecessary here).
"""

import logging

from chimera.controllers.ws.gateway import GatewayCore
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.constants import MANAGER_LOCATION

log = logging.getLogger(__name__)


class WsGateway(ChimeraObject):
    __config__ = {
        "ws_host": "0.0.0.0",
        "ws_port": 7667,
        # max concurrent in-flight bus calls (long-running instrument methods
        # each hold one executor thread until they answer)
        "max_calls": 64,
    }

    def __init__(self):
        ChimeraObject.__init__(self)
        self._core: GatewayCore | None = None

    def __start__(self):
        self._core = GatewayCore(
            bus=self.__bus__,
            gateway_url=self.get_location(),
            manager_url=f"{self.__bus__.url.bus}{MANAGER_LOCATION}",
            ws_host=self["ws_host"],
            ws_port=self["ws_port"],
            max_calls=self["max_calls"],
            standalone=False,
        )
        self._core.start()
        return True

    def __stop__(self):
        if self._core is not None:
            self._core.stop()
            self._core = None
        return True
