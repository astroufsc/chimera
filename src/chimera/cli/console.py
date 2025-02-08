#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

if __name__ == "__main__":

    # import sys

    from chimera.core.manager import Manager
    from chimera.controllers.console import Console

    manager = Manager()
    manager.addClass(Console, "console", start=True)
    manager.wait()
