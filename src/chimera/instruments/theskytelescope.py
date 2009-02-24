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

from chimera.core.site import Site

from chimera.util.coord    import Coord

from chimera.instruments.telescope import TelescopeBase
from chimera.instruments.focuser   import FocuserBase

from chimera.interfaces.telescope  import PositionOutsideLimitsException
from chimera.interfaces.focuser    import FocuserFeature


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


class TheSkyTelescope (TelescopeBase, FocuserBase):

    __config__ = {"thesky": [5, 6],
                  'site':   '/Site/0'}

    def __init__ (self):
        TelescopeBase.__init__ (self)
        FocuserBase.__init__ (self)

        self._thesky = None
        self._telescope = None
        self._term = threading.Event ()
        self._idle_time = 0.2
        self._target = None

        self._supports = {FocuserFeature.TEMPERATURE_COMPENSATION: False,
                          FocuserFeature.POSITION_FEEDBACK: False,
                          FocuserFeature.ENCODER: False}

        try:
            self._site = self.getManager().getProxy(self['site'])
            self._gotSite=True
        except:
            self._site = Site()
            self._gotSite=False

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
            #kill -9 on Windows
            time.sleep(2)
            subprocess.call("TASKKILL /IM Sky.exe /F")
        else:
            time.sleep(2)
            subprocess.call("TASKKILL /IM TheSky6.exe /F")
                    

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
        self._telescope.GetRaDec()
        # FIXME: returns Position (pickle error)
        return (Coord.fromHMS(self._telescope.dRa),
                Coord.fromDMS(self._telescope.dDec))

    @com
    def getPositionAltAz (self):
        self._telescope.GetAzAlt ()
        # FIXME: returns Position (pickle error)
        return (Coord.fromDMS(self._telescope.dAlt),
                Coord.fromDMS(self._telescope.dAz))

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
        self._telescope.SetTracking(1,0,1,0)

    @com
    def stopTracking (self):
        self._telescope.SetTracking(0,0,0,0)


    def _getSite(self):
        if self._gotSite:
            self._site._transferThread()
            return self._site
        else:
            try:
                self._site = self.getManager().getProxy(self['site'])
                self._gotSite=True
            except:
                pass
        return self._site
    
    @com
    def moveEast (self, offset, slewRate = None):
#        newRa = self.getRa() + Coord.fromH(offset/3600)
#        self.slewToRaDec(Position.fromRaDec(newRa, self.getDec()))
        self._telescope.Jog(offset / 60, 'East')

    @com
    def moveWest (self, offset, slewRate = None):
#        newRa = self.getRa() - Coord.fromH(offset/3600)
#        self.slewToRaDec(Position.fromRaDec(newRa, self.getDec()))
        self._telescope.Jog(offset / 60, 'West')

    @com
    def moveNorth (self, offset, slewRate = None):
#        newDec = self.getDec() + Coord.fromD(offset/3600)
#        self.slewToRaDec(Position.fromRaDec(self.getRa(),newDec))
        self._telescope.Jog(offset / 60, 'North')

    @com
    def moveSouth (self, offset, slewRate = None):
#        newDec = self.getDec() - Coord.fromD(offset/3600)
#        self.slewToRaDec(Position.fromRaDec(self.getRa(),newDec))
        self._telescope.Jog(offset / 60, 'South')
    
    def moveIn (self, n):
        """
        Move the focuser IN by n steps.

        Driver should interpret n as whatever it support (time pulse
        or absolute encoder positions).  if only time pulse is
        available, driver must use pulse_in_multiplier as a multiple
        to determine how much time the focuser will move
        IN. pulse_in_multiplier and n will be in miliseconds.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  n: int
        @param n: Number of steps to move IN.

        @rtype   : None
        """
        while(n > 1000):
            n-=1000
            self._telescope.FocusInFast()
        while(n > 0):
            n-=1
            self._telescope.FocusInSlow()
        


    def moveOut (self, n):
        """
        Move the focuser OUT by n steps.

        Driver should interpret n as whatever it support (time pulse
        or absolute encoder positions).  if only time pulse is
        available, driver must use pulse_out_multiplier as a multiple
        to determine how much time the focuser will move
        OUT. pulse_out_multiplier and n will be in miliseconds.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  n: int
        @param n: Number of steps to move OUT.

        @rtype   : None
        """
        while(n > 1000):
            n-=1000
            self._telescope.FocusOutFast()
        while(n > 0):
            n-=1
            self._telescope.FocusOutSlow()

    def moveTo (self, position):
        """
        Move the focuser to the select position.

        If the focuser doesn't support absolute position movement, it
        MUST return False.

        @note: Drivers must raise InvalidFocusPositionException if the
        request position couldn't be achived.

        @type  position: int
        @param position: Position to move the focuser.

        @rtype   : None
        """
        return False

    def getPosition (self):
        """
        Gets the current focuser position.

        @note: If the driver doesn't support position readout it MUST
        raise NotImplementedError.

        @rtype   : int
        @return  : Current focuser position.
        """
        raise NotImplementedError()
        
    
    def getRange (self):
        """Gets the focuser total range
        @rtype: tuple
        @return: Start and end positions of the focuser (start, end)
        """
        return (0,0)
