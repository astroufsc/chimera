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

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.telescope import ITelescopeDriver

import logging
import sys

if sys.platform == "win32":

    import win32com.client
    from pywintypes import com_error

else:

    logging.warning ("Not on win32. Paramount will not works.")


class Paramount (BasicLifeCycle, ITelescopeDriver):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.com_tel  = None
        self.com_sky  = None
        self.com_util = None

    # life cycle
    def init (self, config):

        self.config += config

        self.com_tel  = win32com.client.Dispatch("TheSky.Telescope")
        self.com_sky  = win32com.client.Dispatch("TheSky.RASCOMTheSky")
        self.com_util = win32com.client.Dispatch("DriverHelper.Util")

        self.com_tel.Connected = True
        self.com_sky.Connect()

        if (self.config.find_home):
            self.com_tel.FindHome()

    def shutdown (self):
        
        if (self.config.park_on_exit):
            self.com_tel.Park()

        self.com_tel.Connected = False
        self.com_sky.Quit()

    def control (self):
        pass

    # methods
    def slew(self, coord):
        
        self.tel.SlewToCoordinates(self.util.HMSToHours(targetRA), self.util.DMSToDegrees(targetDEC))

    def abortSlew(self):
        pass

    def moveAxis(self, axis, offset):
        pass
