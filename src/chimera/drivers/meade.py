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

import time
import serial
import signal
import threading
import logging
import datetime

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.telescope import (ITelescopeDriver, ITelescopeDriverSlew,
                                          ITelescopeDriverSync, ITelescopeDriverPark)

from chimera.util.coord import Coord, Ra, Dec, Lat, Long, Alt, Az, SkyPoint, LocalPoint

class Meade (BasicLifeCycle,
             ITelescopeDriver, ITelescopeDriverSlew,
             ITelescopeDriverSync, ITelescopeDriverPark):

    ALT_AZ = 0
    POLAR  = 1
    LAND   = 2

    alignModes = {ALT_AZ: "ALT_AZ",
                  POLAR : "POLAR",
                  LAND  : "LAND"}

    GUIDE  = 0
    CENTER = 1
    FIND   = 2
    MAX    = 3

    slewRates = {GUIDE : "GUIDE",
                 CENTER: "CENTER",
                 FIND  : "FIND",
                 MAX   : "MAX"}

    def __init__(self, manager):

        BasicLifeCycle.__init__ (self, manager)

        self._tty = None
        self._slewRate = None
        self._abort = threading.Event ()
        self._slewing = False

        self._errorNo = 0
        self._errorString = ""

        self._lastAlignMode = None
        self._parked = False

        self._target_az = None
        self._target_alt = None        
        

    # -- IBasicLifeCycle implementation --

    def init (self, config):

        self.config += config

        if not self.open ():
            return False

        return True

    def shutdown (self):

        if not self.close ():
            return False

        return True

    def main (self):
        pass


    # -- ITelescopeDriver implementation

    def _checkMeade (self):

        tmp = self._tty.timeout
        self._tty.timeout = 5

        align = self.getAlignMode ()

        self._tty.timeout = tmp


        if align < 0:
            self.setError (-1, "Couldn't found a Meade telescope on '%s'." % self.device)
            return False

        return True

    def open(self):

        self._tty = serial.Serial()
        self.device = self.config.device

        self._tty.port = self.device
        self._tty.timeout = self.config.timeout

        try:
            self._tty.open()

            if not self._checkMeade():
                logging.warning ("Couldn't found a Meade telescope on %s." %  self.config.device)
                return False

            #if self.config.auto_align:
            #    self.autoAlign ()

            # FIMXE: set alignment mode, date, time, lat, long
            if not self.setAlignMode (eval('Meade.%s' % self.config.align_mode)):
                return False

            # activate HPP (high precision poiting) we really need this!!
            if not self._setHighPrecision ():
                logging.warning ("This scope doesn't support High Precison pointing. Errors comming :(")
                return False

            # set default slew rate
            self.setSlewRate (Meade.MAX)

            return True

        except serial.SerialException, e:
            self.setError (-1, str(e))
            logging.warning ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception (e)
            return False

        except IOError,e:
            self.setError(e)
            logging.warning ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception (e)
            return False

    def close(self):
        if self._tty.isOpen():
            self._tty.close()
            return True
        else:
            self.setError(-1, "Device not open")
            return False

    # --

    def autoAlign (self):

        self._write (":Aa#")

        while not self._tty.inWaiting ():
            time.sleep (1)

        # FIXME: bad LX200 behaviour
        tmp = self._read (1)

        return True

    def getAlignModes(self):
        return Meade.alignModes

    def getAlignMode(self):

        self._write('\x06') # ACK

        ret = self._read (1)

        # damn stupid '0' at the start of the mode
        if ret == '0':
            ret = self._read (1, flush=False)

        if not ret:
            self.setError (-1, "Couldn't get the alignment mode. Is this a Meade??")
            return False

        if ret == "A":
            return Meade.ALT_AZ
        elif ret == "P":
            return Meade.POLAR
        elif ret == "L":
            return Meade.LAND
        else:
            self.setError (-1, "Couldn't get the alignment mode. Is this a Meade??")
            return False

    def setAlignMode(self, mode):

        if mode not in self.getAlignModes().keys():
            self.setError (-1, "Invalid alignment mode '%s'." % mode)
            return False

        if mode == self.getAlignMode():
            return True

        if mode == Meade.ALT_AZ:
            self._write (":AA#")
        elif mode == Meade.POLAR:
            self._write (":AP#")
        elif mode == Meade.LAND:
            self._write (":AL#")
        else:
            self.setError (-1, "Invalid alignment mode '%s'." % mode)
            return False

        return True


    def isSlewing(self):
        return self._slewing
    
    def slewToRaDec(self, ra, dec):

        # FIXME: validate limits?

        if self.isSlewing ():
            self.setError (-1, "Telescope already slewing.")
            return False

        if not self.setTargetRaDec(ra, dec):
            return False

        if not self._slewToRaDec():
            return False

        return True

    def _slewToRaDec(self):

        self._slewing = True
        self._abort.clear ()

        # slew
        self._write(':MS#')

        # to handle timeout
        start_time = time.time()

        err = self._readbool()

        if err:
            # check error message
            msg = self._readline()
            self.setError(-1, msg[:-1])
            self._slewing = False
            return False

        # slew possible
        target = self.getTargetRaDec()

        while True:

            # check slew abort event
            if self._abort.isSet ():
                self.setError (-1, "Slew aborted")
                self._slewing = False
                return False

            # check timeout
            if time.time () >= (start_time + self.config.max_slew_time):
                self._abortSlew ()
                self.setError (-1, "Slew aborted. Max slew time reached.")
                self._slewing = False
                return False

            position = self.getPositionRaDec()

            if target.near (position, "00 01 00"):
                time.sleep (self.config.stabilization_time)
                self._slewing = False
                return True

            time.sleep (self.config.slew_idle_time)


    def slewToAzAlt(self, az, alt):

        if self.isSlewing ():
            self.setError (-1, "Telescope already slewing.")
            return False

        if not self.setTargetAzAlt (az, alt):
            return False

        if not self._slewToAzAlt():
            return False

        return True

    def _slewToAzAlt(self):

        self._slewing = True
        self._abort.clear ()

        # slew
        self._write(':MA#')

        # to handle timeout
        start_time = time.time()

        err = self._readbool()

        if err:
            # check error message
            self.setError(-1, "Couldn't slew to AZ: '%s' ALT: '%s'." % self.getTargetAzAlt())
            self._slewing = False
            return False

        # slew possible
        target = self.getTargetAzAlt()

        while True:

            # check slew abort event
            if self._abort.isSet ():
                self.setError (-1, "Slew aborted")
                self._slewing = False
                return False

            # check timeout
            if time.time () >= (start_time + self.config.max_slew_time):
                self._abortSlew ()
                self.setError (-1, "Slew aborted. Max slew time reached.")
                self._slewing = False
                return False

            position = self.getPositionAzAlt()

            #if target.near (position, "00 01 00"):
            #    time.sleep (self.config.stabilization_time)
            #    self._slewing = False
            #    return True

            time.sleep (self.config.slew_idle_time)


    def abortSlew(self):

        if not self.isSlewing():
            return False

        err = self._write (":Q#")

        if err:
            self.setError (-1, "Error aborting slew.")
            return False

        self._abort.set()

    def _move (self, direction, duration=0.0, slewRate = None):

        # FIXME: concurrent slew commands? YES.. it should works!
        if self.isSlewing():
            self.setError (-1, "Telescope is slewing. Cannot move.") # REALLY? no.
            return False

        if slewRate:
            self.setSlewRate (slewRate)

        start = time.time ()
        self._write (":M%s#" % direction)

        finish = start + duration

        while time.time() < finish:
            time.sleep (0.01) # 0.15' resolution

        # FIXME: slew limits
        if duration:
            self._stopMove (direction)

        return True

    def _stopMove (self, direction):
        self._write (":Q%s#" % direction)

        # FIXME: stabilization time depends on the slewRate!!!
        if self.getSlewRate() == Meade.GUIDE:
            time.sleep (0.1)
            return True

        elif self.getSlewRate() == Meade.CENTER:
            time.sleep (0.2)
            return True

        elif self.getSlewRate() == Meade.FIND:
            time.sleep (0.3)
            return True

        elif self.getSlewRate() == Meade.MAX:
            time.sleep (0.4)
            return True

    def moveEast (self, duration=0.0, slewRate = None):
        return self._move ("e", duration, slewRate)

    def moveWest (self, duration=0.0, slewRate = None):
        return self._move ("w", duration, slewRate)

    def moveNorth (self, duration=0.0, slewRate = None):
        return self._move ("n", duration, slewRate)

    def moveSouth (self, duration=0.0, slewRate = None):
        return self._move ("s", duration, slewRate)

    def stopMoveEast (self):
        return self._stopMove ("e")

    def stopMoveWest (self):
        return self._stopMove ("w")

    def stopMoveNorth (self):
        return self._stopMove ("n")

    def stopMoveSouth (self):
        return self._stopMove ("s")

    def stopMoveAll (self):
        self._write (":Q#")
        return True

    def getRa(self):

        self._write(":GR#")
        ret = self._readline()

        return Ra(ret[:-1])

    def getDec(self):
        self._write(":GD#")
        ret = self._readline()

        ret = ret.replace('\xdf', ':')

        return Dec(ret[:-1])

    def getPositionRaDec(self):
        return SkyPoint(self.getRa(), self.getDec())

    def getPositionAzAlt(self):
        return LocalPoint(self.getAz(), self.getAlt())

    def getTargetRaDec(self):
        return SkyPoint(self.getTargetRa(), self.getTargetDec())

    def getTargetAzAlt(self):
        return LocalPoint(self.getTargetAz(), self.getTargetAlt())

    def setTargetRaDec(self, ra, dec):

        if not self.setTargetRa (ra):
            return False

        if not self.setTargetDec (dec):
            return False

        return True

    def setTargetAzAlt(self, az, alt):

        if not self.setTargetAz (az):
            return False

        if not self.setTargetAlt (alt):
            return False

        return True

    def getTargetRa(self):

        self._write(":Gr#")
        ret = self._readline()

        return Ra(ret[:-1])

    def setTargetRa(self, ra):

        if not isinstance (ra, Ra):
            ra = Ra (ra)

        self._write(":Sr%s#" % ra.hor(hsep="\xdf", msep=":", sign=True))

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid RA '%s'" % ra)
            return False

        return True

    def setTargetDec(self, dec):

        if not isinstance (dec, Dec):
            dec = Dec (dec)

        self._write(":Sd%s#" % dec.sexagesimal(dsep="\xdf", msep=":", sign=True))

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid DEC '%s'" % dec)
            return False

        return True

    def getTargetDec(self):
        self._write(":Gd#")
        ret = self._readline()

        ret = ret.replace('\xdf', ':')

        return Dec(ret[:-1])

    def getAz(self):
        self._write(":GZ#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord(ret[:-1])

    def getAlt(self):
        self._write(":GA#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord(ret[:-1])

    def getTargetAlt(self):
        return self._target_alt
    
    def setTargetAlt(self, alt):

        if not isinstance (alt, Alt):
            alt = Alt (alt)

        s = alt.sexagesimal(dsep="\xdf", msep=":", sign=True)
        s = s[:s.rfind('.')]

        if float(s[s.find(":")+1:]) == 0.0:
            s = s[:s.find(":")] + ":00"

        self._write(":Sa%s#" % s)

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid Altitude '%s'" % alt)
            return False

        self._target_alt = alt
        
        return True

    def getTargetAz(self):
        return self._target_az
    
    def setTargetAz(self, az):

        if not isinstance (az, Az):
            az = Az (az)

        # strange conversion to get Meade happy
        s = az.sexagesimal(dsep="\xdf", msep=":", sign=False)
        s = s[:s.rfind(".")]

        if len(s) == 8:
            s = "0" + s

        self._write (":Sz%s#" % s)

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid Azimuth '%s'" % s)
            return False

        self._target_az = az

        return True


    def getLat(self):
        self._write(":Gt#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')[:-1]

        # FIXME bug on parsing 22:32
        ret += ":00"

        return Lat(ret)

    def setLat (self, coord):

        if not isinstance (coord, Lat):
            coord = Lat (coord)

        lat = coord.sexagesimal(dsep="\xdf", msep="#", sign=True)
        lat = lat[:lat.rfind("#")]

        self._write (":St%s#" % lat)

        ret = self._readbool ()

        if not ret:
            self.setError(-1, "Invalid Latitude '%s'" % lat)
            return False

        return True

    def getLong(self):
        self._write(":Gg#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')[:-1]

        # FIXME bug on parsing 22:32
        ret += ":00"

        return Long(ret)

    def setLong (self, coord):

        if not isinstance (coord, Long):
            coord = Long (coord)

        # strange conversion to get Meade happy
        long = abs(coord.decimal())
        long = Long (long)
        long = long.sexagesimal(dsep="\xdf", msep="#")
        long = long[:long.find("#")]

        if len(long) == 5:
            long = "0"+long

        self._write (":Sg%s#" % long)

        ret = self._readbool ()
        if not ret:
            self.setError(-1, "Invalid Longitude '%s'" % long)
            return False

        return True

    def getDate(self):
        self._write(":GC#")
        ret = self._readline()

        # FIXME: better date representation
        #ret = ret.split ("/")
        #date = datetime.date (year=int(ret[2]), month=int(ret[0]), day=int(ret[1]))

        return ret[:-1]

    def setDate (self, time):

        now = datetime.date.fromtimestamp(time)

        date = now.strftime ("%m/%d/%y")
        self._write (":SC%s#" % date)

        ret = self._read (1)

        if ret == "0":
            self.setError (-1, "Couldn't set date, invalid format '%s'" % date)

            # discard junk null byte
            self._read (1)

            return False

        elif ret == "1":
            # discard junk message and wait Meade finish update of internal databases
            self._tty.timeout = 60
            self._readline () # junk message

            self._readline ()

            return True

    def getLocalTime(self):
        self._write(":GL#")
        ret = self._readline()
        return ret[:-1]

    def setLocalTime (self, local):

        local = datetime.datetime.fromtimestamp (local)
        local = local.strftime ("%H:%M:%S")

        self._write (":SL%s#" % local)

        ret = self._readbool ()
        if not ret:
            self.setError (-1, "Invalid local time '%s'." % local)
            return False

        return True

    def getLocalSiderealTime(self):
        self._write(":GS#")
        ret = self._readline()
        return ret[:-1]

    def setLocalSiderealTime (self, local):
        local = datetime.datetime.fromtimestamp (local)
        local = local.strftime ("%H:%M:%S")

        self._write (":SS%s#" % local)

        ret = self._readbool ()
        if not ret:
            self.setError (-1, "Invalid Local sidereal time '%s'." % local)
            return False

        return True

    def getUTCOffset(self):
        self._write(":GG#")
        ret = self._readline()
        return ret[:-1]

    def setUTCOffset (self, offset):

        offset = "%+02.1f" % offset

        self._write (":SG%s#" % offset)

        ret = self._readbool ()
        if not ret:
            self.setError (-1, "Invalid UTC offset '%s'." % offset)
            return False

        return True


    def getCurrentTrackingRate (self):

        self._write(":GT#")

        ret = self._readline()

        if not ret:
            return False

        ret = float (ret[:-1])

        return ret

    def setCurrentTrackingRate (self, trk):

        trk = "%02.1f" % trk

        if len (trk) == 3:
            trk = "0" + trk

        self._write(":ST%s#" % trk)

        ret = self._readbool()

        if not ret:
            self.setError (-1, "Invalid tracking rate '%s'." % trk)
            return False

        self._write(":TM#")

        return ret

    def startTracking (self):

        if self.getAlignMode() in (Meade.POLAR, Meade.ALT_AZ):
            return True

        if not self.setAlignMode (self._lastAlignMode):
            return False

        return True

    def stopTracking (self):


        if self.getAlignMode() == Meade.LAND:
            return True

        self._lastAlignMode = self.getAlignMode ()        

        if not self.setAlignMode (Meade.LAND):
            return False

        return True

    def _setHighPrecision (self):

        self._write (":GR#")
        ret = self._readline ()[:-1]

        if len (ret) == 7: # low precision
            self._write (":U#")

        return True

    # -- ITelescopeDriverSync implementation --

    def sync(self, ra, dec):

        if not self.setTargetRaDec (ra, dec):
            return False

        self._write(":CM#")

        ret = self._readline ()

        if not ret:
            self.setError (-1, "Error syncing on '%s' '%s'." % (ra, dec))

        #self.syncComplete (self.getPosition)

        return True

    def getSlewRates (self):
        return Meade.slewRates

    def setSlewRate (self, rate):

        if rate not in self.getSlewRates().keys():
            self.setError ("Invalid slew rate '%s'." % rate)
            return False

        if rate == Meade.GUIDE:
            self._write (":RG#")
        elif rate == Meade.CENTER:
            self._write (":RC#")
        elif rate == Meade.FIND:
            self._write (":RM#")
        elif rate == Meade.MAX:
            self._write (":Sw%d#" % self.config.max_slew_rate)
            self._write (":RS#")
        else:
            self.setError ("Invalid slew rate '%s'." % rate)
            return False

        self._slewRate = rate

        return True

    def getSlewRate (self):
        return self._slewRate

    # -- park

    def getParkPosition (self):
        return (self.config.park_position_alt, self.config.park_position_az)

    def setParkPosition (self, alt, az):

        return True

        #if not isinstance(alt, Alt):
        #    alt = Alt (alt)

        #if not isinstance(az, Az):
        #    az = Az (az)
                
        #self.config.park_position_alt = alt.decimal()
        #self.config.park_position_az  = az.decimal()        

        #return True

    def isParked (self):
        return self._parked
                
    def park (self):

        if self.isParked ():
            self.setError (-1, "Telescope already parked.")
            return False

        # 1. slew to park position
        if not self.slewToRaDec(self.getLocalSiderealTime(), "00:00:00"):
            return False

        # 2. stop tracking
        if not self.stopTracking ():
            return False

        # 3. power off
        #if not self.powerOff ():
        #    return False

        self._parked = True

        return True

    def unpark (self):

        if not self.isParked():
            self.setError (-1, "Telescope is not parked.")
            return False

        # 1. power on
        #if not self.powerOn ():
        #    return False

        # 2. start tracking
        if not self.startTracking ():
            return False

        # 3. set location, date and time
        # FIXME: global config for site data
        if not self.setLat("-22 32 03"):
            return False

        if not self.setLong("-45 34 57"):
            return False
       
        if not self.setDate(time.time ()):
            return False

        if not self.setLocalTime(time.time ()):
            return False
            
        if not self.setUTCOffset(3):
            return False

        # 4. sync on park position (not really necessary when parking on DEC=0, RA=LST
        # convert from park position to RA/DEC using the last LST set on 2.
        #ra = 0
        #dec = 0
        
        #if not self.sync (ra, dec):
        #    return False

        self._parked = False

        return True


    # low-level

    def _read(self, n = 1, flush = True):
        if not self._tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        if flush:
            self._tty.flushInput()

        return self._tty.read(n)

    def _readline(self, eol='#'):
        if not self._tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        return self._tty.readline(None, eol)

    def _readbool(self, n = 1):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _write(self, data, flush = True):
        if not self._tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        if flush:
            self._tty.flushOutput()

        return self._tty.write(data)


    def setError(self, errorNo, errorString):
        self._errorNo = errorNo
        self._errorString = errorString

    def getError(self):
        if self._errorNo:
            ret = (self._errorNo, self._errorString)
        else:
            ret = 0

        self._errorNo = 0
        self._errorString = ""

        return ret
