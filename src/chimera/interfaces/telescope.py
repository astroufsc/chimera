#! /usr/bin/python
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


from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.util.enum  import Enum


SlewRate = Enum ("MAX",
                 "GUIDE")


class ITelescope (Interface):
    """
    Telescope base interface.
    """

    __options__ = {"driver": "/Fake/telescope",

                   "limits": "limits.filename",
                   
                   "model"           : "Fake Telescopes Inc.",
                   "optics"          : ["Newtonian", "SCT", "RCT"],
                   "mount"           : "Mount type Inc.",
                   "aperture"        : 100.0,  # mm
                   "focal_length"    : 1000.0, # mm
                   "focal_reduction" : 1.0,    # unit (ex., 0.5 for a half length focal reducer)
                   }


class ITelescopeSlew (ITelescope):
    """Basic interface for telescopes.
    """

    def slewToObject (self, name):
        """Slew the scope to the the coordinates of the given object.

        @param name: Object name to slew to.
        @type  name: str

        @return: False if slew failed, True otherwise.
        @rtype: bool
        """

    def slewToRaDec (self, ra, dec, epoch = "J2000"):
        """Slew the scope to the given {ra} and {dec} on the given {epoch}

        @param ra: the Right Ascension to slew to in sexagesimal hours (hh:mm:ss).
        @type  ra: str, float or int
        
        @param dec: the Declination to slew to in sexagesimal degress (+-dd:mm:ss).
        @type  dec: str, float or int

        @param epoch: The Epoch of the given coordinates. The coordinative will be processed to reflect the real
                      coordinates at the day of the observation (in other words, will be precessed).
                      Accepts a str with the equinox specification (J or B) and a date with optional day/month
                      specification, like 2000.1, or, just an int/float with the date (Julian equinox will be assumed).

        @type  epoch: str, int or float
        
        @return: False if slew failed, True otherwise.
        @rtype: bool
        """

    def slewToAzAlt (self, az, alt):
        """Slew to the given Azimuth and Altitude.

        @param az: Azimuth
        @type alt: int or float

        @param alt: Altitude
        @type az: int or float

        @return: False if slew failed, True otherwise
        @rtype: bool
        """

    def abortSlew (self):
        """Try to abort the current slew.

        @return: False if slew couldn't be aborted, True otherwise.
        @rtype: bool
        """

    def isSlewing (self):
        """Ask if the telescope is slewing right now.

        @return: True if the telescope is slewing, False otherwise.
        @rtype: bool
        """

    def moveEast (self, offset, rate=SlewRate.MAX):
        """Move the scope {offset} arcseconds East (if offset positive, West otherwise)

        @param offset: Arcseconds to move East.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: True if succesfull, False otherwise.
        @rtype: bool

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def moveWest (self, offset, rate=SlewRate.MAX):
        """Move the scope {offset} arcseconds West (if offset positive, East otherwise)

        @param offset: Arcseconds to move West.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: True if succesfull, False otherwise.
        @rtype: bool

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def moveNorth (self, offset, rate=SlewRate.MAX):
        """Move the scope {offset} arcseconds North (if offset positive, South otherwise)

        @param offset: Arcseconds to move North.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: True if succesfull, False otherwise.
        @rtype: bool

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def moveSouth (self, offset, rate=SlewRate.MAX):
        """Move the scope {offset} arcseconds South (if offset positive, North otherwise)

        @param offset: Arcseconds to move South.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: True if succesfull, False otherwise.
        @rtype: bool

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def getRa (self):
        """Get the current telescope Right Ascension (RA).

        @return: Telescope's current RA (decimal degrees).
        @rtype: float
        """
    
    def getDec (self):
        """Get the current telescope Declination (Dec).

        @return: Telescope's current Dec (decimal degrees).
        @rtype: float
        """

    def getAz (self):
        """Get the current telescope Azimuth (Az)

        @return: Telescope's current Az (decimal degrees)
        @rtype: float
        """

    def getAlt (self):
        """Get the current telescope Altitude (Alt)

        @return: Telescope's current Alt (decimal degrees).
        @rtype: float
        """

    def getPosition (self):
        """Get the current position of the telescope.

        @return: Telescope's current target (ra, dec) in decimal degrees tuple.
        @rtype: tuple
        """

    def getTarget (self):
        """Get the current telescope target.

        @return: Telescope's current target (ra, dec) in decimal degrees tuple.
        @rtype: tuple
        """

    @event
    def slewStart (self, target):
        """Indicates that a slew operation started.

        @param target: The target position where the telescope will slew
                       to. (ra, dec) decimal degrees tuple.
        
        @type target: tuple
        """

    @event
    def slewComplete (self, position):
        """Indicates that the last slew operation finished (with or without success).

        @param position: The telescope current position when the slew finished ((ra, dec) in decimal degrees).
        @type  position: tuple
        """

    @event
    def abortComplete (self, position):
        """Indicates that the last slew operation was aborted.

        @param position: The telescope position when the scope aborted ((ra, dec) in decimal degrees).
        @type  position: tuple
        """


class ITelescopeSync (ITelescope):
    """Telescope with sync support.
    """

    def syncRaDec (self, ra, dec):
        """Synchronizes the telescope on the given coordinates.

        This mean different things to different telescopes, but the general idea is that after
        this command, the logical position that the telescope will return when asked about will be {ra} and {dec}.

        @param ra: the Right Ascension to sync in sexagesimal hours (hh:mm:ss).
        @type  ra: str, float or int
        
        @param dec: the Declination to sync in sexagesimal degress (+-dd:mm:ss).
        @type  dec: str  float or int
        """

    def syncObject (self, name):
        """Synchronize the telescope using the coordinates of the given object.
        
        @param name: Object name to sync in.
        @type  name: str
        """
    
    @event
    def syncComplete(self, position):
        """Fired when a synchronization operation finishes.

        @param position: The position where the telescope synced in ((ra, dec) in decimal degrees).
        @type  position: tuple
        """


class ITelescopePark (ITelescope):
    """Telescope with park/unpark support.
    """

    __options__ = {"default_park_position_az": 180.0,
                   "default_park_position_alt": 90.0}

        
    def park(self):
        """Park the telescope on the actual park position (L{setParkPosition}).

        When parked, the telescope will not track objects and maybe turned off (if the scope was able to).

        @return: True if successfull, False otherwise.
        @rtype : bool
        """

    def unpark (self):
        """Wake up the telescope of the last park operation.
        
        @return: True if successfull, False otherwise.
        @rtype : bool
        """

    def setParkPosition (self, az, alt):
        """Defines where the scope will park when asked to.

        @param az: Azimuth
        @type alt: int or float

        @param alt: Altitude
        @type az: int or float

        @return: True if successfull, False otherwise.
        @rtype : bool
        """

    @event
    def parkComplete(self):
        """Indicates that the scope has parked successfuly.
        """

    @event
    def unparkComplete (self):
        """Indicates that the scope has unparked (waked up) successfuly.
        """
