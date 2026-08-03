# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

# the classloader imports module <clsname.lower()>: "type: WsGateway" in
# chimera.config lands here, the implementation lives in the ws package
from chimera.controllers.ws.controller import WsGateway as WsGateway
