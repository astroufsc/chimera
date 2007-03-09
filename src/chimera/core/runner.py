#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

import os
import sys
import signal
import threading

# ============
# FIXME Ugly hacks to python threading works with signal
# FIXME see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
# FIXME see http://greenteapress.com/semaphores/

# FIXME run shutdown on exit
# FIXME log

class RunnerWin32 (object):

    def __init__ (self, obj):
        self.obj = obj

    def main (self):
        self.obj.init ()


class RunnerPosix (object):

    def __init__ (self, obj):
        self.obj = obj

        self.mainPID = os.getpid()


    def main(self):

        # FIXME: shutdown = threading.Event ()

        # from here we will have 2 process. Child process will return from splitAndWatch,
        # while the main process will watch for signals and will kill the child
        # process.

        self.splitAndWatch()

        pid = os.getpid ()

        # run obj.init on child process
        if pid != self.mainPID:
            self.obj.init ()


    def splitAndWatch(self):

        child = os.fork()

        if child == 0:
            return

        self.childPID = child

        signal.signal(signal.SIGTERM, self.sighandler)
        signal.signal(signal.SIGINT, self.sighandler)

        try:
            os.wait()
            self.kill()

        except OSError:
            pass

    def kill(self):
        os.kill (self.childPID, signal.SIGKILL)

    def sighandler(self, sig, frame):
        self.kill()

# win32 doesn't support POSIX fork (arghh!)

if sys.platform == "win32":
    Runner = RunnerWin32
else:
    Runner = RunnerPosix
