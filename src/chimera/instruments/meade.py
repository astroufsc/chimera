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
import os
import os
import socket

try:
    import cPickle as pickle
except ImportError:
    import pickle

import serial

from chimera.instruments.telescope import TelescopeBase
from chimera.interfaces.telescope  import SlewRate, AlignMode, TelescopeStatus

from chimera.util.coord    import Coord
from chimera.util.position import Position, Epoch
from chimera.util.enum     import Enum

from chimera.core.lock  import lock
from chimera.core.exceptions import ObjectNotFoundException, MeadeException
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

Direction = Enum("E", "W", "N", "S")


class Meade (TelescopeBase):
    
    __config__ = {'azimuth180Correct'   : True,
                  'method': 'serial:/dev/ttyS1'}

    def __init__(self):

        TelescopeBase.__init__ (self)

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

        # debug log
        self._debugLog = None
        try:
            self._debugLog = open(os.path.join(SYSTEM_CONFIG_DIRECTORY, "meade-debug.log"), "w")
        except IOError, e:
            self.log.warning("Could not create meade debug file (%s)" % str(e))

        # how much arcseconds / second for every slew rate
        # and direction
        self._calibration = {}
        self._calibration_time = 5.0
        self._calibrationFile = os.path.join(SYSTEM_CONFIG_DIRECTORY, "move_calibration.bin")
        
        for rate in SlewRate:
            self._calibration[rate] = {}
            for direction in Direction:
                self._calibration[rate][direction] = 1

    # -- ILifeCycle implementation --

    def __start__ (self):
        self.open()

        # try to read saved calibration data
        if os.path.exists(self._calibrationFile):
            try:
                self._calibration = pickle.loads(open(self._calibrationFile, "r").read())
                self.calibrated = True
            except Exception, e:
                self.log.warning("Problems reading calibration persisted data (%s)" % e)

        return True

    def __stop__ (self):

        if self.isSlewing():
            self.abortSlew()

        self.close()

    def __main__ (self):
        pass

    # -- ITelescope implementation

    def _checkMeade (self):
        if self._tty:
            tmp = self._tty.timeout
            self._tty.timeout = 5

        align = self.getAlignMode ()

        if self._tty:
            self._tty.timeout = tmp

        if align < 0:
            raise MeadeException ("Couldn't find a Meade telescope on '%s'." % self["device"])

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
            self.setLocalTime(dt.datetime.now().time())
            self.setUTCOffset(site.utcoffset())
            self.setDate(dt.date.today())
        except ObjectNotFoundException:
            self.log.warning("Cannot initialize telescope. "
                             "Site object not available. Telescope"
                             " attitude cannot be determined.")

    @lock
    def open(self):
        params = self["device"]
        try:
            if params[0] == 'serial':
                self._tty = serial.Serial(params[1],
                                          baudrate=9600,
                                          bytesize=serial.EIGHTBITS,
                                          parity=serial.PARITY_NONE,
                                          stopbits=serial.STOPBITS_ONE,
                                          timeout=self["timeout"],
                                          xonxoff=False, rtscts=False)
                self._tty.open()
            elif params[0] == 'eth':
                self._tty = None
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((params[1], int(params[2]))

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
        if self._tty:
            if self._tty.isOpen():
                self._tty.close()
                return True
            else:
                return False
        else:
            self.sock.close()

    # --

    @lock
    def autoAlign (self):

        self._write (":Aa#")

        if self._tty:
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

        self._readbool()

        return True

    @lock
    def slewToRaDec(self, position):

        self._validateRaDec(position)

        if self.isSlewing():
            # never should happens 'cause @lock
            raise MeadeException("Telescope already slewing.")

        self.setTargetRaDec(position.ra, position.dec)

        status = TelescopeStatus.OK
        
        try:
            status = self._slewToRaDec()
            return True
        finally:
            self.slewComplete(self.getPositionRaDec(), status)

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
    def slewToAltAz(self, position):

        self._validateAltAz(position)

        self.setSlewRate(self["slew_rate"])

        if self.isSlewing ():
            # never should happens 'cause @lock
            raise MeadeException("Telescope already slewing.")

        lastAlignMode = self.getAlignMode()

        self.setTargetAltAz (position.alt, position.az)

        status = TelescopeStatus.OK

        try:
            self.setAlignMode(AlignMode.ALT_AZ)
            status = self._slewToAltAz()
            return True
        finally:
            self.slewComplete(self.getPositionRaDec(), status)
            self.setAlignMode(lastAlignMode)

        return False

    def _slewToAltAz(self):

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
            raise MeadeException("Couldn't slew to ALT/AZ: '%s'." % self.getTargetAltAz())

        # slew possible
        target = self.getTargetAltAz()

        return self._waitSlew(start_time, target, local=True)

    def _waitSlew (self, start_time, target, local=False):

        self.slewBegin(target)

        while True:

            # check slew abort event
            if self._abort.isSet ():
                self._slewing = False
                return TelescopeStatus.ABORTED

            # check timeout
            if time.time () >= (start_time + self["max_slew_time"]):
                self.abortSlew ()
                self._slewing = False
                raise MeadeException("Slew aborted. Max slew time reached.")

            if local:
                position = self.getPositionAltAz()
            else:
                position = self.getPositionRaDec()

            if target.within (position, eps=Coord.fromAS(60)):
                time.sleep (self["stabilization_time"])
                self._slewing = False
                return TelescopeStatus.OK

            time.sleep (self["slew_idle_time"])

        return TelescoopeStatus.ERROR

    def abortSlew(self):

        if not self.isSlewing():
            return True

        self._abort.set()

        self.stopMoveAll()

        time.sleep (self["stabilization_time"])

    def isSlewing(self):
        return self._slewing

    def _move (self, direction, duration=1.0, slewRate = SlewRate.GUIDE):

        if duration <= 0:
            raise ValueError ("Slew duration cannot be less than 0.")

        # FIXME: concurrent slew commands? YES.. it should works!
        if self.isSlewing():
            raise MeadeException("Telescope is slewing. Cannot move.") # REALLY? no.

        if slewRate:
            self.setSlewRate (slewRate)

        startPos = self.getPositionRaDec()

        self._slewing = True
        self._write (":M%s#" % str(direction).lower())

        start = time.time ()
        finish = start + duration

        self.log.debug("[move] delta: %f s" % (finish-start,))

        while time.time() < finish:
            pass # busy wait!

        # FIXME: slew limits
        self._stopMove (direction)
        self._slewing = False

        def calcDelta(start, end):
            return Coord.fromD(end.angsep(start))

        delta = calcDelta(startPos, self.getPositionRaDec())
        self.log.debug("[move] moved %f arcsec" % delta.AS)

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
        return os.path.exists(self._calibrationFile)

    @lock
    def calibrateMove (self):

        # FIXME: move to a safe zone to do calibrations.
        def calcDelta(start, end):
            return end.angsep(start)

        def calibrate(direction, rate):
            start = self.getPositionRaDec()
            self._move(direction, self._calibration_time, rate)
            end = self.getPositionRaDec()

            return calcDelta(start, end)
            
        for rate in SlewRate:
            for direction in Direction:
                self.log.debug("Calibrating %s %s" % (rate, direction))

                total = 0

                for i in range(2):
                    total += calibrate(direction, rate).AS

                self.log.debug("> %f" % (total/2.0)) 
                self._calibration[rate][direction] = total/2.0

        # save calibration
        try:
            f = open(self._calibrationFile, "w")
            f.write(pickle.dumps(self._calibration))
            f.close()
        except Exception, e:
            self.log.warning("Problems persisting calibration data. (%s)" % e)

        self.log.info("Calibration was OK.")

    def _calcDuration (self, arc, direction, rate):
        """
        Calculates the time spent (returned number) to move by arc in a 
        given direction at a given rate
        """

        if not self.isMoveCalibrated():
            self.log.info("Telescope fine movement not calibrated. Calibrating now...")
            self.calibrateMove()

        self.log.debug("[move] asked for %s arcsec" % float(arc))
                   
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
    def getPositionAltAz(self):
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def getTargetRaDec(self):
        return Position.fromRaDec(self.getTargetRa(), self.getTargetDec())

    @lock
    def getTargetAltAz(self):
        return Position.fromAltAz(self.getTargetAlt(), self.getTargetAz())

    @lock
    def setTargetRaDec(self, ra, dec):

        self.setTargetRa (ra)
        self.setTargetDec (dec)

        return True

    @lock
    def setTargetAltAz(self, alt, az):

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

        self._write(":Sd%s#" % dec.strfcoord("%(d)02d\xdf%(m)02d:%(s)02d"))

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
        
        c = Coord.fromDMS(ret[:-1])
        
        if self['azimuth180Correct']:
            if c.toD() >= 180:
                c = c - Coord.fromD(180)
            else:
                c = c + Coord.fromD(180)

        return c

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

        self._write(":Sa%s#" % alt.strfcoord("%(d)02d\xdf%(m)02d\'%(s)02d"))

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

        if self['azimuth180Correct']:
            
            if az.toD() >= 180:
                az = az - Coord.fromD(180)
            else:
                az = az + Coord.fromD(180)

        self._write (":Sz%s#" % az.strfcoord("%(d)03d\xdf%(m)02d:%(s)02d", signed=False))

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
            if self._tty:
                tmpTimeout = self._tty.timeout
                self._tty.timeout = 60
            self._readline () # junk message

            self._readline ()

            if self._tty:
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

    # -- ITelescopeSync implementation --

    @lock
    def syncRaDec(self, position):

        self.setTargetRaDec (position.ra, position.dec)

        self._write(":CM#")

        ret = self._readline ()

        if not ret:
            raise MeadeException("Error syncing on '%s' '%s'." % (position.ra, position.dec))

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
            self._write (":Sw4#")
            if not self._readbool():
                raise ValueError("Invalid slew rate")

            self._write (":RS#")
        else:
            raise ValueError("Invalid slew rate '%s'." % rate)

        self._slewRate = rate

        return True

    def getSlewRate (self):
        return self._slewRate

    # -- park

    def getParkPosition (self):
        return Position.fromAltAz(self["park_position_alt"],
                                  self["park_position_az"])

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

        # 1. slew to park position FIXME: allow different park
        # positions and conversions from ra/dec -> az/alt

        site = self.getManager().getProxy("/Site/0")

        self.slewToRaDec(Position.fromRaDec(str(self.getLocalSiderealTime()),
                                            site["latitude"]))

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

        # 4. sync on park position (not really necessary when parking
        # on DEC=0, RA=LST

        # convert from park position to RA/DEC using the last LST set on 2.
        #ra = 0
        #dec = 0

        #if not self.sync (ra, dec):
        #    return False

        self.unparkComplete()

        self._parked = False

        return True


    # low-level

    def _debug(self, msg):
        if self._debugLog:
            print >> self._debugLog, time.time(), threading.currentThread().getName(), msg
            self._debugLog.flush()

    def _read(self, n = 1, flush = True):
        if self._tty:
            if not self._tty.isOpen():
                raise IOError("Device not open")
            
            if flush:
                self._tty.flushInput()
                
            ret = self._tty.read(n)
            self._debug("[read ] %s" % repr(ret))
            return ret
        else:
            ret = self.sock.read(n)
            self._debug("[read ] %s" % repr(ret))
            return ret

    def _readline(self, eol='#'):
        if self._tty:
            if not self._tty.isOpen():
                raise IOError("Device not open")
        
            ret = self._tty.readline(None, eol)
            self._debug("[read ] %s" % repr(ret))
            return ret
        else:
            sio = io.TextIOWrapper(self.sock, newline=eol)
            ret = sio.readline()
            self._debug("[read ] %s" % repr(ret))
            return ret

    def _readbool(self):

        try:
            ret = int(self._read(1))
        except ValueError:
            return False

        if not ret:
            return False

        return True

    def _write(self, data, flush = True):
        self._debug("[write] %s" % repr(data))

        if self._tty:
            if not self._tty.isOpen():
                raise IOError("Device not open")
            
            if flush:
                self._tty.flushOutput()
                
            return self._tty.write(data)
        else:
            return self.sock.write(data)

