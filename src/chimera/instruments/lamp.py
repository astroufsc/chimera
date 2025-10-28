# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
# SPDX-FileCopyrightText: 2006-present Antonio Kanaan <kanaan@astro.ufsc.br>

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.lock import lock
from chimera.interfaces.lamp import LampSwitch


class LampBase(ChimeraObject, LampSwitch):
    def __init__(self):
        ChimeraObject.__init__(self)

    @lock
    def switch_on(self):
        raise NotImplementedError()

    @lock
    def switch_off(self):
        raise NotImplementedError()

    def is_switched_on(self):
        raise NotImplementedError()
