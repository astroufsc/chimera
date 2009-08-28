
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

from chimera.core.exceptions import ChimeraException
from chimera.core.lock     import lock

from chimera.util.coord    import Coord
from chimera.util.position import Position
from chimera.util.enum     import Enum

from chimera.instruments.telescope import TelescopeBase
from chimera.instruments.dcfocuser import DCFocuser
from chimera.interfaces.telescope  import PositionOutsideLimitsException

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
            raise ChimeraException(str(e))

    return com_wrapper


Direction = Enum("IN", "OUT")


class TheSkyTelescope (TelescopeBase, DCFocuser):

    __config__ = {"thesky": [5, 6]}

    def __init__ (self):
        TelescopeBase.__init__ (self)
        DCFocuser.__init__(self)

        self._thesky = None
        self._telescope = None
        self._term = threading.Event ()
        self._idle_time = 0.2
        self._target = None

    @com
    def __start__ (self):
        self.open()
        super(TheSkyTelescope, self).__start__()
        return True

    @com
    def __stop__ (self):
        self.close()
        super(TheSkyTelescope, self).__stop__()        
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
            #kill -9 on Windows
            time.sleep(2)
            subprocess.call("TASKKILL /IM Sky.exe /F")
        else:
            time.sleep(2)
            subprocess.call("TASKKILL /IM TheSky6.exe /F")
                    

    @com
    def getRa (self):
        self._telescope.GetRaDec()
        return Coord.fromH(self._telescope.dRa)

    @com
    def getDec (self):
        self._telescope.GetRaDec()
        return Coord.fromD(self._telescope.dDec)

    @com
    def getAz (self):
        self._telescope.GetAzAlt()
        return Coord.fromD(self._telescope.dAz)

    @com
    def getAlt (self):
        self._telescope.GetAzAlt()
        return Coord.fromD(self._telescope.dAlt)

    @com
    def getPositionRaDec (self):
        self._telescope.GetRaDec()
        return Position.fromRaDec(Coord.fromH(self._telescope.dRa), Coord.fromD(self._telescope.dDec))

    @com
    def getPositionAltAz (self):
        self._telescope.GetAzAlt ()
        return Position.fromAltAz(Coord.fromD(self._telescope.dAlt), Coord.fromD(self._telescope.dAz))

    @com
    def getTargetRaDec (self):
        if not self._target: return self.getPositionRaDec()
        return self._target

    @com
    def slewToRaDec (self, position):

        if self.isSlewing ():
            return False

        self._target = position
        self._term.clear ()

        try:
            self._telescope.Asynchronous = 1

            position_now = self._getFinalPosition(position)
            
            self.slewBegin((position_now.ra, position_now.dec))
            self._telescope.SlewToRaDec (position_now.ra.H, position_now.dec.D, "chimera")

            while not self._telescope.IsSlewComplete:

                if self._term.isSet ():
                    return True

                time.sleep (self._idle_time)

            self.slewComplete(self.getPositionRaDec())

        except com_error:
            raise PositionOutsideLimitsException("Position outside limits.")

        return True

#    @com
#    def slewToAltAz (self, position):
#
#        if self.isSlewing ():
#            return False
#
#        #self._target = position
#        self._term.clear ()
#
#        try:
#            self._telescope.Asynchronous = 1
#            self.slewBegin((position.ra, position.dec))
#            self._telescope.SlewToAltAz (position.alt.D, position.az.D, "chimera")
#
#            while not self._telescope.IsSlewComplete:
#
#                if self._term.isSet ():
#                    return True
#
#                time.sleep (self._idle_time)
#
#            self.slewComplete(self.getPositionRaDec())
#
#        except com_error:
#            raise PositionOutsideLimitsException("Position outside limits.")
#
#        return True

    @com
    def abortSlew (self):

        if self.isSlewing ():
            
            #TODO:Where do we use this?! We are failing lint since self.term is undefined
            self.term.set ()
            time.sleep (self._idle_time)
            self._telescope.Abort ()
            return True

        return False

    @com
    def isSlewing (self):
        return (self._telescope.IsSlewComplete == 0)

    @com
    def isTracking (self):
        return (self._telescope.IsTracking == 1)

    @com
    def park (self):
        self._telescope.Park()

    @com
    def unpark (self):
        self._telescope.Connect()
        self._telescope.FindHome()

    @com
    def isParked (self):
        return False

    @com
    def startTracking (self):
        self._telescope.SetTracking(1,1,0,0)

    @com
    def stopTracking (self):
        self._telescope.SetTracking(0,1,0,0)

    @com
    def moveEast (self, offset, slewRate = None):
        self._telescope.Asynchronous = 0
        self._telescope.Jog(offset.AS / 60.0, 'East')
        self._telescope.Asynchronous = 1        

    @com
    def moveWest (self, offset, slewRate = None):
        self._telescope.Asynchronous = 0
        self._telescope.Jog(offset.AS / 60.0, 'West')
        self._telescope.Asynchronous = 1        

    @com
    def moveNorth (self, offset, slewRate = None):
        self._telescope.Asynchronous = 0
        self._telescope.Jog(offset.AS / 60.0, 'North')
        self._telescope.Asynchronous = 1        

    @com
    def moveSouth (self, offset, slewRate = None):
        self._telescope.Asynchronous = 0
        self._telescope.Jog(offset.AS / 60.0, 'South')
        self._telescope.Asynchronous = 1

    @lock
    def syncRaDec(self, position):
        self._telescope.Sync (position.ra.H, position.dec.D, "chimera")
        self.syncComplete(position)            

    #
    # focuser implementation
    #
    
    def _move (self, direction, steps):

        pulses = int(steps * self["dt"])

        if direction == Direction.IN:
            method = self._telescope.FocusInSlow
        else:
            method = self._telescope.FocusOutSlow
            
        for i in pulses:
            method()
    
    def getRange (self):
        """Gets the focuser total range
        @rtype: tuple
        @return: Start and end positions of the focuser (start, end)
        """
        return (0,0)

    def getMetadata (self, request):
        headers = []
        headers += super(TelescopeBase, self).getMetadata(request)
        headers += super(DCFocuser, self).getMetadata(request)
        return headers

