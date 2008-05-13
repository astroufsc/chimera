#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import logging
import logging.handlers
import sys
import os
import os.path


# try to use fatser (C)StringIO, use slower one if not available
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


from chimera.core.exceptions import printException


__all__ = ['setConsoleLevel']


class ChimeraFormatter (logging.Formatter):

    def __init__ (self, fmt, datefmt):
        logging.Formatter.__init__(self, fmt, datefmt)

    def formatException (self, exc_info):
        stream = StringIO.StringIO()
        printException(exc_info[1], stream=stream)

        try:
            return stream.getvalue()
        finally:
            stream.close()

        
fmt = ChimeraFormatter(fmt='%(asctime)s.%(msecs)d %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s',
                       datefmt='%d-%m-%Y %H:%M:%S')

try:
    if not os.path.exists(os.path.expanduser("~/.chimera")):
        os.mkdir(os.path.expanduser("~/.chimera/"))
except Exception:
    pass

fileHandler = None

try:
    fileHandler = logging.handlers.RotatingFileHandler(os.path.expanduser("~/.chimera/chimera.log"),
                                                       maxBytes=5*1024*1024, backupCount=10)
except Exception:
    pass

consoleHandler = logging.StreamHandler(sys.stderr)

if fileHandler:
    fileHandler.setFormatter(fmt)
    fileHandler.setLevel(logging.DEBUG)

consoleHandler.setFormatter(fmt)
consoleHandler.setLevel(logging.WARNING)

root = logging.getLogger("chimera")
root.setLevel(logging.DEBUG)

if fileHandler:
    root.addHandler(fileHandler)
    
root.addHandler(consoleHandler)


def setConsoleLevel (level):
    consoleHandler.setLevel(level)
