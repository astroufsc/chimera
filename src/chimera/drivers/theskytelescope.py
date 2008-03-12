#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

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

from chimera.util.coord    import Coord
from chimera.util.position import Position

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions    import ChimeraException

from chimera.interfaces.telescope       import PositionOutsideLimitsException
from chimera.interfaces.telescopedriver import ITelescopeDriverSlew

log = logging.getLogger(__name__)


if sys.platform == "win32":
    # handle COM multithread support
    # see: Python Programming On Win32, Mark Hammond and Andy Robinson, Appendix D
    #      http://support.microsoft.com/kb/q150777/
    sys.coinit_flags = 0 # pythoncom.COINIT_MULTITHREAD
    import pythoncom

    from win32com.client import Dispatch
    from pywintypes import com_error

else:
    log.warning("Not on win32. TheSky Telescope will not work.")
    #raise ChimeraException("Not on win32. TheSky Telescope will not work.")    


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


class TheSkyTelescope (ChimeraObject, ITelescopeDriverSlew):

    __config__ = {"thesky": [5, 6]}

    def __init__ (self):
        ChimeraObject.__init__ (self)

        self._thesky = None
        self._telescope = None
        self._term = threading.Event ()
        self._idle_time = 0.2
        self._target = None

    @com
    def __start__ (self):
        self.open()
        return True

    @com
    def __stop__ (self):
        self.close()
        return True

    @com
    def open (self):

        try:
            if self["thesky"] == 6:
                self._thesky = Dispatch ("TheSky6.RASCOMTheSky")
                self._telescope = Dispatch ("TheSky6.RASCOMTele")
            else:
                self._thesky = Dispatch ("TheSky.RASCOMTheSky")
                self._telescope = Dispatch ("TheSky.RASCOMTele")

        except com_error:
            self.log.error ("Couldn't instantiate TheSky %d COM objects." % self["thesky"])
            return False

        try:

            if self["thesky"] == 6:
                self._thesky.Connect ()
                self._telescope.Connect ()
                self._telescope.FindHome ()
            else:
                self._thesky.Connect ()
                self._telescope.Connect ()
                
            return True
        
        except com_error, e:
            self.log.error ("Couldn't connect to TheSky. (%s)" % e)
            return False

    @com
    def close (self):
        try:
            self._thesky.Disconnect ()
            self._thesky.DisconnectTelescope ()
            self._telescope.Disconnect ()
            self._thesky.Quit ()
        except com_error:
            self.log.error ("Couldn't disconnect to TheSky.")
            return False

        if self["thesky"] == 5:
            # kill -9 on Windows
            subprocess.call("TASKKILL /IM Sky.exe /F")
        
            

    @com
    def getRa (self):
        self._telescope.GetRaDec()
        return Coord.fromHMS(self._telescope.dRa)

    @com
    def getDec (self):
        self._telescope.GetRaDec()
        return Coord.fromDMS(self._telescope.dDec)

    @com
    def getAz (self):
        self._telescope.GetAzAlt()
        return Coord.fromDMS(self._telescope.dAz)

    @com
    def getAlt (self):
        self._telescope.GetAzAlt()
        return Coord.fromDMS(self._telescope.dAlt)

    @com
    def getPositionRaDec (self):
        self._telescope.GetRaDec ()
        # FIXME: returns Position (pickle error)
        return (Coord.fromHMS(self._telescope.dRa),
                Coord.fromDMS(self._telescope.dDec))

    @com
    def getTargetRaDec (self):
        if not self._target: return (0, 0)

        return (self._target.ra, self._target.dec)

    @com
    def slewToRaDec (self, position):

        if self.isSlewing ():
            return False

        self._target = position
        self._term.clear ()

        try:
            self._telescope.Asynchronous = 1
            self.slewBegin((position.ra, position.dec))
            self._telescope.SlewToRaDec (position.ra.H, position.dec.D, "chimera")

            while not self._telescope.IsSlewComplete:

                if self._term.isSet ():
                    return True

                time.sleep (self._idle_time)

            self.slewComplete(self.getPositionRaDec())

        except com_error:
            raise PositionOutsideLimitsException("Position outside limits.")

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

