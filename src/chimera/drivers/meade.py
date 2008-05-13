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

import time
import threading
import datetime as dt
from types import FloatType

import serial

from chimera.core.chimeraobject         import ChimeraObject

from chimera.interfaces.telescopedriver import ITelescopeDriverSlew
from chimera.interfaces.telescopedriver import ITelescopeDriverSync
from chimera.interfaces.telescopedriver import ITelescopeDriverPark
from chimera.interfaces.telescopedriver import ITelescopeDriverTracking
from chimera.interfaces.telescopedriver import SlewRate, AlignMode

from chimera.util.coord    import Coord
from chimera.util.position import Position
from chimera.util.enum     import Enum

from chimera.core.lock  import lock

from chimera.core.exceptions import ChimeraException, ObjectNotFoundException


class MeadeException(ChimeraException):
    pass


Direction = Enum("E", "W", "N", "S")


class Meade (ChimeraObject,
             ITelescopeDriverSlew,
             ITelescopeDriverSync,
             ITelescopeDriverPark,
             ITelescopeDriverTracking):

    def __init__(self):

        ChimeraObject.__init__ (self)

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

        # how much arcseconds / second for every slew rate
        # and direction
        self._calibration = {}
        self._calibration_time = 2.0
        
        for rate in SlewRate:
            self._calibration[rate] = {}
            for direction in Direction:
                self._calibration[rate][direction] = 1

        self._calibrated = False


    # -- ILifeCycle implementation --

    def __start__ (self):
        self.open()

    def __stop__ (self):

        if self.isSlewing():
            self.abortSlew()

        self.close()

    def __main__ (self):
        pass

    # -- ITelescopeDriver implementation

    def _checkMeade (self):

        tmp = self._tty.timeout
        self._tty.timeout = 5

        align = self.getAlignMode ()

        self._tty.timeout = tmp

        if align < 0:
            raise MeadeException ("Couldn't found a Meade telescope on '%s'." % self["device"])

        return True

    def _initTelescope (self):

        self.setAlignMode(self["align_mode"])

        # activate HPP (high precision poiting). We really need this!!
        self._setHighPrecision()

        # set default slew rate
        self.setSlewRate(self["slew_rate"])

        try:
            site = self.getManager().getProxy("/Site/0")

            self.setLat(site["latitude"])
            self.setLong(site["longitude"])
            self.setDate(dt.date.today())
            self.setLocalTime(dt.datetime.now().time())
            self.setUTCOffset(site["utc_offset"])
        except ObjectNotFoundException:
            self.log.warning("Cannot initialize telescope. "
                             "Site object not available. Telescope"
                             " attitude cannot be determined.")

    @lock
    def open(self):

        self._tty = serial.Serial(self["device"],
                                  baudrate=9600,
                                  bytesize=serial.EIGHTBITS,
                                  parity=serial.PARITY_NONE,
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=self["timeout"],
                                  xonxoff=False, rtscts=False)

        try:
            self._tty.open()

            self._checkMeade()

            #if self["auto_align"]:
            #    self.autoAlign ()

            # manualy initialize scope
            if self["skip_init"]:
                self.log.info("Skipping init as requested.")
            else:
                self._initTelescope()

            return True

        except (serial.SerialException, IOError), e:
            raise MeadeException("Error while opening %s." % self["device"])

    @lock
    def close(self):
        if self._tty.isOpen():
            self._tty.close()
            return True
        else:
            return False

    # --

    @lock
    def autoAlign (self):

        self._write (":Aa#")

        while not self._tty.inWaiting ():
            time.sleep (1)

        # FIXME: bad LX200 behaviour
        tmp = self._read (1)

        return True

    @lock
    def getAlignMode(self):

        self._write('\x06') # ACK

        ret = self._read (1)

        # damn stupid '0' at the start of the mode
        if ret == '0':
            ret = self._read (1, flush=False)

        if not ret or ret not in "APL":
            raise MeadeException("Couldn't get the alignment mode. Is this a Meade??")

        if ret == "A":
            return AlignMode.ALT_AZ
        elif ret == "P":
            return AlignMode.POLAR
        elif ret == "L":
            return AlignMode.LAND

    @lock
    def setAlignMode(self, mode):

        if mode == self.getAlignMode():
            return True

        if mode == AlignMode.ALT_AZ:
            self._write (":AA#")
        elif mode == AlignMode.POLAR:
            self._write (":AP#")
        elif mode == AlignMode.LAND:
            self._write (":AL#")

        return True


    def isSlewing(self):
        return self._slewing

    @lock
    def slewToRaDec(self, position):

        if self.isSlewing():
            # never should happens 'cause @lock
            raise MeadeException("Telescope already slewing.")

        self.setTargetRaDec(position.ra, position.dec)

        if self._slewToRaDec():
            self.slewComplete(self.getPositionRaDec())
            return True

        return False


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
            self._slewing = False
            raise MeadeException(msg[:-1])

        # slew possible
        target = self.getTargetRaDec()

        return self._waitSlew(start_time, target)

    @lock
    def slewToAzAlt(self, position):

        if self.isSlewing ():
            # never should happens 'cause @lock
            raise MeadeException("Telescope already slewing.")

        self.setTargetAzAlt (position.az, position.alt)

        if self._slewToAzAlt():
            self.slewComplete(self.getPositionRaDec())
            return True

        return False

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
            self._slewing = False
            raise MeadeException("Couldn't slew to AZ/ALT: '%s'." % self.getTargetAzAlt())

        # slew possible
        target = self.getTargetAzAlt()

        return self._waitSlew(start_time, target, local=True)

    def _waitSlew (self, start_time, target, local=False):

        self.slewBegin(target)

        while True:

            # check slew abort event
            if self._abort.isSet ():
                self._slewing = False
                return False

            # check timeout
            if time.time () >= (start_time + self["max_slew_time"]):
                self.abortSlew ()
                self._slewing = False
                raise MeadeException("Slew aborted. Max slew time reached.")

            if local:
                position = self.getPositionAzAlt()
            else:
                position = self.getPositionRaDec()

            if target.within (position, 60, units='arcsec'):
                time.sleep (self["stabilization_time"])
                self._slewing = False
                return True

            time.sleep (self["slew_idle_time"])

        return True

    def abortSlew(self):

        if not self.isSlewing():
            return True

        self._abort.set()

        self.stopMoveAll()

        time.sleep (self["stabilization_time"])

        self.abortComplete(self.getPositionRaDec())

    def _move (self, direction, duration=1.0, slewRate = None):

        if duration <= 0:
            raise ValueError ("Slew duration cannot be less than 0.")

        # FIXME: concurrent slew commands? YES.. it should works!
        if self.isSlewing():
            raise MeadeException("Telescope is slewing. Cannot move.") # REALLY? no.

        if slewRate:
            self.setSlewRate (slewRate)

        self._slewing = True
        start = time.time ()
        self._write (":M%s#" % str(direction).lower())

        finish = start + duration

        while time.time() < finish:
            time.sleep (0.01) # 0.15' resolution

        # FIXME: slew limits
        self._stopMove (direction)
        self._slewing = False

        return True

    def _stopMove (self, direction):
        self._write (":Q%s#" % str(direction).lower())

        rate = self.getSlewRate()
        # FIXME: stabilization time depends on the slewRate!!!
        if rate == SlewRate.GUIDE:
            time.sleep (0.1)
            return True

        elif rate == SlewRate.CENTER:
            time.sleep (0.2)
            return True

        elif rate == SlewRate.FIND:
            time.sleep (0.3)
            return True

        elif rate == SlewRate.MAX:
            time.sleep (0.4)
            return True

    def isMoveCalibrated (self):
        return self._calibrated

    @lock
    def calibrateMove (self):

        # FIXME: move to a safe zone to do calibrations.
        # FIXME: save calibration data to database to not need to do it
        # every time

        def calcDelta(start, end):
            return end.angsep(start)

        def calibrate(direction, rate):
            start = self.getPositionRaDec()
            self._move(direction, self._calibration_time, rate)
            end = self.getPositionRaDec()

            return calcDelta(start, end)
            
        for rate in SlewRate:
            for direction in Direction:

                total = 0

                for i in range(3):
                    total += calibrate(direction, rate).arcsec()
                
                self._calibration[rate][direction] = total/3.0

    def _calcDuration (self, arc, direction, rate):
        return arc*(self._calibration_time/self._calibration[rate][direction])

    @lock
    def moveEast (self, offset, slewRate = None):
        return self._move (Direction.E,
                           self._calcDuration(offset, Direction.E, slewRate),
                           slewRate)

    @lock
    def moveWest (self, offset, slewRate = None):
        return self._move (Direction.W,
                           self._calcDuration(offset, Direction.W, slewRate),
                           slewRate)

    @lock
    def moveNorth (self, offset, slewRate = None):
        return self._move (Direction.N,
                           self._calcDuration(offset, Direction.N, slewRate),
                           slewRate)

    @lock
    def moveSouth (self, offset, slewRate = None):
        return self._move (Direction.S,
                           self._calcDuration(offset, Direction.S, slewRate),
                           slewRate)

    @lock
    def stopMoveEast (self):
        return self._stopMove (Direction.E)

    @lock
    def stopMoveWest (self):
        return self._stopMove (Direction.W)

    @lock
    def stopMoveNorth (self):
        return self._stopMove (Direction.N)

    @lock
    def stopMoveSouth (self):
        return self._stopMove (Direction.S)

    @lock
    def stopMoveAll (self):
        self._write (":Q#")
        return True

    @lock
    def getRa(self):
        self._write(":GR#")
        ret = self._readline()

        # meade bugs: sometimes, after use Move commands, getRa
        # returns a 1 before the RA, so we just check this and discard
        # it here
        if len(ret) > 9:
            ret = ret[1:]
        
        return Coord.fromHMS(ret[:-1])

    @lock
    def getDec(self):
        self._write(":GD#")
        ret = self._readline()

        # meade bugs: same as getRa
        if len(ret) > 10:
            ret = ret[1:]

        ret = ret.replace('\xdf', ':')

        return Coord.fromDMS(ret[:-1])

    @lock
    def getPositionRaDec(self):
        return Position.fromRaDec(self.getRa(), self.getDec())

    @lock
    def getPositionAzAlt(self):
        return Position.fromAzAlt(self.getAz(), self.getAlt())

    @lock
    def getTargetRaDec(self):
        return Position.fromRaDec(self.getTargetRa(), self.getTargetDec())

    @lock
    def getTargetAzAlt(self):
        return Position.fromAzAlt(self.getTargetAz(), self.getTargetAlt())

    @lock
    def setTargetRaDec(self, ra, dec):

        self.setTargetRa (ra)
        self.setTargetDec (dec)

        return True

    @lock
    def setTargetAzAlt(self, az, alt):

        self.setTargetAz (az)
        self.setTargetAlt (alt)

        return True

    @lock
    def getTargetRa(self):

        self._write(":Gr#")
        ret = self._readline()

        return Coord.fromHMS(ret[:-1])

    @lock
    def setTargetRa(self, ra):

        if not isinstance (ra, Coord):
            ra = Coord.fromHMS(ra)

        self._write(":Sr%s#" % ra.strfcoord("%(h)02d\xdf%(m)02d:%(s)02d"))

        ret = self._readbool()

        if not ret:
            raise MeadeException("Invalid RA '%s'" % ra)

        return True

    @lock
    def setTargetDec(self, dec):

        if not isinstance (dec, Coord):
            dec = Coord.fromDMS(dec)

        self._write(":Sd%s#" % dec.strfcoord("%(d)+02d\xdf%(m)02d:%(s)02d"))

        ret = self._readbool()

        if not ret:
            raise MeadeException("Invalid DEC '%s'" % dec)

        return True

    @lock
    def getTargetDec(self):
        self._write(":Gd#")
        ret = self._readline()

        ret = ret.replace('\xdf', ':')

        return Coord.fromDMS(ret[:-1])

    @lock
    def getAz(self):
        self._write(":GZ#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord.fromDMS(ret[:-1])

    @lock
    def getAlt(self):
        self._write(":GA#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord.fromDMS(ret[:-1])

    def getTargetAlt(self):
        return self._target_alt

    @lock
    def setTargetAlt(self, alt):

        if not isinstance (alt, Coord):
            alt = Coord.fromD (alt)

        self._write(":Sa%s#" % alt.strfcoord("%(d)+02d\xdf%(m)02d:%(s)02d"))

        ret = self._readbool()

        if not ret:
            raise MeadeException("Invalid Altitude '%s'" % alt)

        self._target_alt = alt

        return True

    def getTargetAz(self):
        return self._target_az

    @lock
    def setTargetAz(self, az):

        if not isinstance (az, Coord):
            az = Coord.fromDMS (az)

        self._write (":Sz%s#" % az.strfcoord("%(d)03d\xdf%(m)02d:%(s)02d"))

        ret = self._readbool()

        if not ret:
            raise MeadeException("Invalid Azimuth '%s'" % az.strfcoord("%(d)03d\xdf%(m)02d"))

        self._target_az = az

        return True

    @lock
    def getLat(self):
        self._write(":Gt#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')[:-1]

        return Coord.fromDMS(ret)

    @lock
    def setLat (self, lat):

        if not isinstance (lat, Coord):
            lat = Coord.fromDMS (lat)

        lat_str = lat.strfcoord("%(d)02d\xdf%(m)02d")

        self._write (":St%s#" % lat_str)

        ret = self._readbool ()

        if not ret:
            raise MeadeException("Invalid Latitude '%s' ('%s')" % (lat, lat_str))

        return True

    @lock
    def getLong(self):
        self._write(":Gg#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')[:-1]

        return Coord.fromDMS(ret)

    @lock
    def setLong (self, coord):

        if not isinstance (coord, Coord):
            coord = Coord.fromDMS (coord)

        self._write (":Sg%s#" % coord.strfcoord("%(d)03d\xdf%(m)02d"))

        ret = self._readbool ()

        if not ret:
            raise MeadeException("Invalid Longitude '%s'" % long)

        return True

    @lock
    def getDate(self):
        self._write(":GC#")
        ret = self._readline()
        return dt.datetime.strptime(ret[:-1], "%m/%d/%y").date()

    @lock
    def setDate (self, date):

        if type(date) == FloatType:
            date = dt.date.fromtimestamp(date)

        self._write (":SC%s#" % date.strftime ("%m/%d/%y"))

        ret = self._read (1)

        if ret == "0":
            # discard junk null byte
            self._read (1)
            raise MeadeException("Couldn't set date, invalid format '%s'" % date)

        elif ret == "1":
            # discard junk message and wait Meade finish update of internal databases
            tmpTimeout = self._tty.timeout
            self._tty.timeout = 60
            self._readline () # junk message

            self._readline ()

            self._tty.timeout = tmpTimeout
            return True

    @lock
    def getLocalTime(self):
        self._write(":GL#")
        ret = self._readline()
        return dt.datetime.strptime(ret[:-1], "%H:%M:%S").time()

    @lock
    def setLocalTime (self, local):

        if type(local) == FloatType:
            local = dt.datetime.fromtimestamp(local).time()

        self._write (":SL%s#" % local.strftime ("%H:%M:%S"))

        ret = self._readbool ()

        if not ret:
            raise MeadeException("Invalid local time '%s'." % local)

        return True

    @lock
    def getLocalSiderealTime(self):
        self._write(":GS#")
        ret = self._readline()
        return dt.datetime.strptime(ret[:-1], "%H:%M:%S").time()

    @lock
    def setLocalSiderealTime (self, local):

        self._write (":SS%s#" % local.strftime ("%H:%M:%S"))

        ret = self._readbool ()

        if not ret:
            raise MeadeException("Invalid Local sidereal time '%s'." % local)

        return True

    @lock
    def getUTCOffset(self):
        self._write(":GG#")
        ret = self._readline()
        return ret[:-1]

    @lock
    def setUTCOffset (self, offset):

        offset = "%+02.1f" % offset

        self._write (":SG%s#" % offset)

        ret = self._readbool ()

        if not ret:
            raise MeadeException("Invalid UTC offset '%s'." % offset)

        return True

    @lock
    def getCurrentTrackingRate (self):

        self._write(":GT#")

        ret = self._readline()

        if not ret:
            raise MeadeException("Couldn't get the tracking rate")

        ret = float (ret[:-1])

        return ret

    @lock
    def setCurrentTrackingRate (self, trk):

        trk = "%02.1f" % trk

        if len (trk) == 3:
            trk = "0" + trk

        self._write(":ST%s#" % trk)

        ret = self._readbool()

        if not ret:
            raise MeadeException("Invalid tracking rate '%s'." % trk)

        self._write(":TM#")

        return ret

    @lock
    def startTracking (self):

        if self.getAlignMode() in (AlignMode.POLAR, AlignMode.ALT_AZ):
            return True

        self.setAlignMode (self._lastAlignMode)
        return True

    @lock
    def stopTracking (self):

        if self.getAlignMode() == AlignMode.LAND:
            return True

        self._lastAlignMode = self.getAlignMode ()
        self.setAlignMode (AlignMode.LAND)
        return True

    def isTracking (self):
        if self.getAlignMode() != AlignMode.LAND:
            return True

        return False

    def _setHighPrecision (self):

        self._write (":GR#")
        ret = self._readline ()[:-1]

        if len (ret) == 7: # low precision
            self._write (":U#")

        return True

    # -- ITelescopeDriverSync implementation --

    @lock
    def syncRaDec(self, position):

        self.setTargetRaDec (position.ra, position.dec)

        self._write(":CM#")

        ret = self._readline ()

        if not ret:
            raise MeadeException("Error syncing on '%s' '%s'." % (ra, dec))

        self.syncComplete (self.getPositionRaDec())

        return True

    @lock
    def setSlewRate (self, rate):

        if rate == SlewRate.GUIDE:
            self._write (":RG#")
        elif rate == SlewRate.CENTER:
            self._write (":RC#")
        elif rate == SlewRate.FIND:
            self._write (":RM#")
        elif rate == SlewRate.MAX:
            self._write (":Sw%d#" % 4)
            self._write (":RS#")
        else:
            raise ValueError("Invalid slew rate '%s'." % rate)

        self._slewRate = rate

        return True

    def getSlewRate (self):
        return self._slewRate

    # -- park

    def getParkPosition (self):
        return Position.fromAzAlt(self["park_position_alt"], self["park_position_az"])

    @lock
    def setParkPosition (self, position):

        self["park_position_az"], self["park_position_alt"] = position.D

        return True

    def isParked (self):
        return self._parked

    @lock
    def park (self):

        if self.isParked ():
            return True

        # 1. slew to park position
        # FIXME: allow different park positions and conversions from ra/dec -> az/alt
        self.slewToRaDec(Position.fromRaDec(str(self.getLocalSiderealTime()),
                                            self.getLatitude()))

        # 2. stop tracking
        self.stopTracking ()

        # 3. power off
        #self.powerOff ()

        self._parked = True

        self.parkComplete()

        return True

    @lock
    def unpark (self):

        if not self.isParked():
            return True
        
        # 1. power on
        #self.powerOn ()

        # 2. start tracking
        self.startTracking()

        # 3. set location, date and time
        self._initTelescope()

        # 4. sync on park position (not really necessary when parking on DEC=0, RA=LST
        # convert from park position to RA/DEC using the last LST set on 2.
        #ra = 0
        #dec = 0

        #if not self.sync (ra, dec):
        #    return False

        self.unparkComplete()

        self._parked = False

        return True


    # low-level

    def _read(self, n = 1, flush = True):

        if not self._tty.isOpen():
            raise IOError("Device not open")

        if flush:
            self._tty.flushInput()

        return self._tty.read(n)

    def _readline(self, eol='#'):
        if not self._tty.isOpen():
            raise IOError("Device not open")

        return self._tty.readline(None, eol)

    def _readbool(self):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _write(self, data, flush = True):
        if not self._tty.isOpen():
            raise IOError("Device not open")

        if flush:
            self._tty.flushOutput()

        return self._tty.write(data)

