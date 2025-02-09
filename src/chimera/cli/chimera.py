#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


def main():

    import sys

    from chimera.controllers.site.main import SiteController

    SiteController(sys.argv).startup()


if __name__ == "__main__":
    main()
