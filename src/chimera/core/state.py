# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.util.enum import Enum


class State(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
