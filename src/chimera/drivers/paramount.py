#! /usr/bin/python
# -*- coding: iso8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2007  P. Henrique Silva <henrique@astro.ufsc.br>

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

import sys
import threading
import subprocess
import logging
import time

from chimera.util.coord import Ra, Dec
from chimera.core.lifecycle import BasicLifeCycle

if sys.platform == "win32":
    # handle COM multithread support
    # see: Python Programming On Win32, Mark Hammond and Andy Robinson, Appendix D
    #      http://support.microsoft.com/kb/q150777/
    sys.coinit_flags = 0 # pythoncom.COINIT_MULTITHREAD
    import pythoncom

    from win32com.client import Dispatch
    from pywintypes import com_error

else:
    logging.warning ("Not on win32. Paramount will not work.")
    sys.exit ("Not on win32. Paramount will not work.")    


def com (func):
    """
    Wrapper decorator used to handle COM objects errors.
    Every method that use COM method should be decorated.
    """
    def com_wrapper (*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except com_error, e:
            raise e

    return com_wrapper


class Paramount (BasicLifeCycle):

    def __init__ (self, manager):

        BasicLifeCycle.__init__ (self, manager)

        self._thesky = None
        self._telescope = None
        self._term = threading.Event ()
        self._idle_time = 0.2
        self._target = (0,0)

    # -- IBasicLifeCycle implementation --

    @com
    def init (self, config):

        self.config += config

        if not self.open ():
            return False

        return True

    @com
    def shutdown (self):

        if not self.close ():
            return False

        return True

    def main (self):
        pass

    # -- ITelescopeDriver implementation -- 

    @com
    def open (self):

        try:
            self._thesky = Dispatch ("TheSky6.RASCOMTheSky")
            self._telescope = Dispatch ("TheSky6.RASCOMTele")
        except com_error:
            logging.error ("Couldn't instantiate TheSky COM objects.")
            return False

        try:
            self._thesky.Connect ()
            self._telescope.Connect ()
            self._telescope.FindHome ()
        except com_error:
            logging.error ("Couldn't connect to TheSky.")
            return False

    @com
    def close (self):
        try:
            self._thesky.Disconnect ()
            self._thesky.DisconnectTelescope ()
            self._telescope.Disconnect ()
            self._thesky.Quit ()
        except com_error:
            logging.error ("Couldn't disconnect to TheSky.")
            return False

    @com
    def getRa (self):
        self._telescope.GetRaDec()
        return self._telescope.dRa

    @com
    def getDec (self):
        self._telescope.GetRaDec()
        return self._telescope.dDec

    @com
    def getAz (self):
        self._telescope.GetAzAlt()
        return self._telescope.dAz

    @com
    def getAlt (self):
        self._telescope.GetAzAlt()
        return self._telescope.dAlt

    @com
    def getPosition (self):
        self._telescope.GetRaDec ()
        return (self._telescope.dRa, self._telescope.dDec)

    @com
    def getTarget (self):
        return self._target

    @com
    def slewToRaDec (self, ra, dec):

        if self.isSlewing ():
            return False

        ra = Ra(ra)
        dec = Dec(dec)

        self._target = (ra, dec)

        self._term.clear ()

        self._telescope.Asynchronous = 1

        self._telescope.SlewToRaDec (ra.decimal()/15.0, dec.decimal(), "chimera")

        while not self._telescope.IsSlewComplete:

            if self._term.isSet ():
                return True

            time.sleep (self._idle_time)

        return True

    @com
    def abortSlew (self):

        if self.isSlewing ():

            self.term.set ()
            time.sleep (self._idle_time)
            self._telescope.Abort ()
            return True

        return False

    @com
    def isSlewing (self):
        return not self._telescope.IsSlewComplete

