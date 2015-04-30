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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import time
import threading
import datetime as dt
#from types import FloatType
import os

try:
    import cPickle as pickle
except ImportError:
    import pickle


from chimera.instruments.telescope import TelescopeBase
from chimera.interfaces.telescope import SlewRate, AlignMode, TelescopeStatus

from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.enum import Enum

from chimera.core.lock import lock
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.util.tpl2 import TPL2,SocketError


Direction = Enum("E", "W", "N", "S")


class AstelcoException(ChimeraException):
    pass


class Astelco (TelescopeBase):  # converted to Astelco

    __config__ = {	'azimuth180Correct': False ,
					'user'	: 'admin',
					'password' : 'admin',
					'ahost' : 'localhost',
					'aport' : '65432'}

    def __init__(self):
        TelescopeBase.__init__(self)

        self._tpl = None
        self._slewRate = None
        self._abort = threading.Event()
        self._slewing = False

        self._errorNo = 0
        self._errorString = ""

        self._lastAlignMode = None
        self._parked = False

        self._target_az = None
        self._target_alt = None
		
        self._ra = None
        self._dec = None
		
        self._az = None
        self._alt = None


        self._poketime = 90.0

        # debug log
        self._debugLog = None
        try:
            self._debugLog = open(
                os.path.join(SYSTEM_CONFIG_DIRECTORY, "astelco-debug.log"), "w")
        except IOError, e:
            self.log.warning("Could not create astelco debug file (%s)" % str(e))

        # how much arcseconds / second for every slew rate
        # and direction
        self._calibration = {}
        self._calibration_time = 5.0
        self._calibrationFile = os.path.join(
            SYSTEM_CONFIG_DIRECTORY, "move_calibration.bin")

        for rate in SlewRate:
            self._calibration[rate] = {}
            for direction in Direction:
                self._calibration[rate][direction] = 1

    # -- ILifeCycle implementation --

    def __start__(self):  # converted to Astelco
        self.open()

        # try to read saved calibration data
        if os.path.exists(self._calibrationFile):
            try:
                self._calibration = pickle.loads(
                    open(self._calibrationFile, "r").read())
                self.calibrated = True
            except Exception, e:
                self.log.warning(
                    "Problems reading calibration persisted data (%s)" % e)

        return True

    def __stop__(self):  # converted to Astelco
        if self.isSlewing():
            self.abortSlew()

        self.close()

    def __main__(self):  # converted to Astelco
        pass

    # -- ITelescope implementation

    def _checkAstelco(self):  # converted to Astelco
        align = self.getAlignMode()

        if int(align) < 0:
            raise AstelcoException(
                "Couldn't find a Astelco telescope on '%s'." % self["device"])

        return True

    def _initTelescope(self):  # converted to Astelco
        self.setAlignMode(self["align_mode"])

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

    def helloTPL(self):
        self.log.debug(self._tpl.getobject('SERVER.UPTIME'))
        self.sayhello = threading.Timer(self._poketime,self.helloTPL)
        self.sayhello.start()

    @lock
    def open(self):  # converted to Astelco
        self.log.info('Connecting to Astelco server %s:%i'%(self["ahost"],
															int(self["aport"])))

        self._tpl = TPL2(user=self["user"],
                        password=self["password"],
                        host=self["ahost"],
                        port=int(self["aport"]),
                        echo=False,
                        verbose=False,
                        debug=True)
        self.log.debug(self._tpl.log)

        try:
            self._tpl #.open()

            self._checkAstelco()

            #if self["auto_align"]:
            #    self.autoAlign ()

            # manualy initialize scope
            if self["skip_init"]:
                self.log.info("Skipping init as requested.")
            else:
                self._initTelescope()

            self._tpl.debug = False
            self.sayhello = threading.Timer(self._poketime,self.helloTPL)
            self.sayhello.start()

            return True

        except (SocketError, IOError):
            raise AstelcoException("Error while opening %s." % self["device"])

    @lock
    def close(self):  # converted to Astelco
        self.sayhello.cancel()
        self.log.debug("TPl2 log:\n")
        for lstr in self._tpl.log:
            self.log.debug(lstr)
        if self._tpl.isListening():
            self._tpl.disconnect()
            return True
        else:
            return False

    # --

    @lock
    def autoAlign(self):  # converted to Astelco

        return True

    @lock
    def getAlignMode(self):  # converted to Astelco
        ret = self._tpl.getobject('TELESCOPE.CONFIG.MOUNTOPTIONS')

        if not ret or ret not in ("AZ-ZD", "ZD-ZD", "HA-DEC"):
            print "Log:"
            print self._tpl.log
            raise AstelcoException(
                "Couldn't get the alignment mode. Is this an Astelco??")

        if ret == "AZ-ZD":
            return AlignMode.ALT_AZ
        elif ret == "HA-DEC":
            return AlignMode.LAND
        else:
            return None

    @lock
    def setAlignMode(self, mode):  # converted to Astelco

        if mode == self.getAlignMode():
            return True
        else:
            return False

    @lock
    def slewToRaDec(self, position):  # no need to convert to Astelco
        self.log.debug('Validating position')
        self._validateRaDec(position)
        self.log.debug('Ok')
        
        self.log.debug("Check if telescope is already slewing")
        if self.isSlewing():
            # never should happens 'cause @lock
            raise AstelcoException("Telescope already slewing.")
        self.log.debug("OK")

        self.log.debug('Setting target RA/DEC')
        self.setTargetRaDec(position.ra, position.dec)
        self.log.debug('Done')
        
        status = TelescopeStatus.OK

        try:
            status = self._slewToRaDec()
            #return True
        finally:
            self._slewing = False
            self.slewComplete(self.getPositionRaDec(), status)

        return status

    def _slewToRaDec(self):  # converted to Astelco
        self._slewing = True
        self._abort.clear()

        # slew
        slewTime = self._tpl.getobject('POINTING.SLEWTIME')
        self.log.info("Time to slew to RA/Dec is reported to be %f s"%( slewTime ))

        target = self.getTargetRaDec()

        return self._waitSlew(time.time(),target,slew_time=slewTime)

    @lock
    def slewToAltAz(self, position):  # no need to convert to Astelco
        self._validateAltAz(position)

        self.setSlewRate(self["slew_rate"])

        if self.isSlewing():
            # never should happens 'cause @lock
            raise AstelcoException("Telescope already slewing.")

        lastAlignMode = self.getAlignMode()

        self.setTargetAltAz(position.alt, position.az)

        status = TelescopeStatus.OK

        try:
            self.setAlignMode(AlignMode.ALT_AZ)
            status = self._slewToAltAz()
            #return True
        finally:
            self.slewComplete(self.getPositionRaDec(), status)
            self.setAlignMode(lastAlignMode)

        return status

    def _slewToAltAz(self):  # converted to Astelco
        self._slewing = True
        self._abort.clear()

        # slew
        print "Time to slew to Alt/Az is reported to be ",
        self._tpl.getobject('POINTING.SLEWTIME'),
        " s."
        
        target = self.getTargetAltAz()

        return self._waitSlew(time.time(), target, local=True)

    def _waitSlew(self, start_time, target, local=False, slew_time=-1):  # converted to Astelco
        self.slewBegin(target)
        
        # Set offset to zero
        
        self.log.debug('SEND: POINTING.TRACK 2')
        cmdid = self._tpl.set('POINTING.TRACK',2,wait=True)
        self.log.debug('PASSED')
        
        err = not self._tpl.succeeded(cmdid)

        if err:
            # check error message
            msg = self._tpl.commands_sent[cmdid]['received']
            self.log.error('Error pointing to %s'%target)
            for line in msg:
                self.log.error(line[:-1])
            self.slewComplete(self.getPositionRaDec(),
                              TelescopeStatus.ERROR)

            return TelescopeStatus.ERROR
    
        self.log.debug('Wait cmd complete...')
        status = self.waitCmd(cmdid,start_time,slew_time)
        self.log.debug('Done')
        
        if not status == TelescopeStatus.OK:
            self.log.warning('Pointing operations failed with status: %s...'%status)
            self.slewComplete(self.getPositionRaDec(),
                              status)
            return status
        
        self.log.debug('SEND: POINTING.TRACK 1')
        cmdid = self._tpl.set('POINTING.TRACK', 1, wait=True)
        self.log.debug('PASSED')
        
        self.log.debug('Wait cmd complete...')
        status = self.waitCmd(cmdid,start_time,slew_time)
        self.log.debug('Done')
        
        # no need to check it here...
        return status


    def waitCmd(self,cmdid,start_time,op_time=-1):

        if op_time < 0:
            op_time = self["max_slew_time"]+1
        
        while not self._tpl.finished(cmdid):

            if self._abort.isSet():
                self._slewing = False
                self.abortSlew()
                self.slewComplete(self.getPositionRaDec(),
                                  TelescopeStatus.ABORTED)
                return TelescopeStatus.ABORTED

            # check timeout
            if time.time() >= (start_time + self["max_slew_time"]):
                self.abortSlew()
                self._slewing = False
                self.log.error('Slew aborted. Max slew time reached.')
                raise AstelcoException("Slew aborted. Max slew time reached.")

            if time.time() >= (start_time + op_time):
                self.log.warning('Estimated slewtime has passed...')
                op_time+=op_time
            
            time.sleep(self["slew_idle_time"])

        return TelescopeStatus.OK

    def abortSlew(self):  # converted to Astelco
        if not self.isSlewing():
            return True

        self._abort.set()

        self.stopMoveAll()

        time.sleep(self["stabilization_time"])

    def isSlewing(self):  # converted to Astelco
        
        # if this is true, then chimera issue a slewing command
        if self._slewing:
            return self._slewing
        # if not, need to check if a external command did that...
        
        self.log.debug('GET TELESCOPE.MOTION_STATE')
        mstate = self._tpl.getobject('TELESCOPE.MOTION_STATE')
        self.log.debug('GET POINTING.TRACK')
        ptrack = self._tpl.getobject('POINTING.TRACK')
        self.log.debug('Done')
        
        self._slewing = (int(mstate) != 0) and (int(ptrack) != 1)
        return self._slewing

    def _move(self, direction, offset, slewRate=SlewRate.GUIDE):  # yet to convert to Astelco

        if self.isSlewing():
            self.log.warning('Telescope is slewing. Stopping current move...')
            self._stopMove()
            #raise AstelcoException("Telescope is slewing. Cannot move.")  # REALLY? no.

        if slewRate:
            self.setSlewRate(slewRate)

        startPos = self.getPositionRaDec()

        self._slewing = True
        #self._write (":M%s#" % str(direction).lower())

        start = time.time()
        finish = start + duration

        self.log.debug("[move] delta: %f s" % (finish-start,))

        while time.time() < finish:
            pass  # busy wait!

        # FIXME: slew limits
        self._stopMove(direction)
        self._slewing = False

        def calcDelta(start, end):
            return Coord.fromD(end.angsep(start))

        delta = calcDelta(startPos, self.getPositionRaDec())
        self.log.debug("[move] moved %f arcsec" % delta.AS)

        return True

    def _stopMove(self, direction):  # yet to convert to Astelco
        #self._write (":Q%s#" % str(direction).lower())
        rate = self.getSlewRate()
        # FIXME: stabilization time depends on the slewRate!!!
        if rate == SlewRate.GUIDE:
            time.sleep(0.1)
            return True

        elif rate == SlewRate.CENTER:
            time.sleep(0.2)
            return True

        elif rate == SlewRate.FIND:
            time.sleep(0.3)
            return True

        elif rate == SlewRate.MAX:
            time.sleep(0.4)
            return True

    def isMoveCalibrated(self):  # no need to convert to Astelco
        return os.path.exists(self._calibrationFile)

    @lock
    def calibrateMove(self):  # no need to convert to Astelco
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

    def _calcDuration(self, arc, direction, rate):  # no need to convert to Astelco
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
    def moveEast(self, offset, slewRate=None):  # no need to convert to Astelco
        return self._move(Direction.E,
                          offset,
                          slewRate)

    @lock
    def moveWest(self, offset, slewRate=None):  # no need to convert to Astelco
        return self._move(Direction.W,
                          offset,
                          slewRate)

    @lock
    def moveNorth(self, offset, slewRate=None):  # no need to convert to Astelco
        return self._move(Direction.N,
                          offset,
                          slewRate)

    @lock
    def moveSouth(self, offset, slewRate=None):  # no need to convert to Astelco
        return self._move(Direction.S,
                          offset,
                          slewRate)

    @lock
    def stopMoveEast(self):  # no need to convert to Astelco
        return self._stopMove(Direction.E)

    @lock
    def stopMoveWest(self):  # no need to convert to Astelco
        return self._stopMove(Direction.W)

    @lock
    def stopMoveNorth(self):  # no need to convert to Astelco
        return self._stopMove(Direction.N)

    @lock
    def stopMoveSouth(self):  # no need to convert to Astelco
        return self._stopMove(Direction.S)

    @lock
    def stopMoveAll(self):  # converted to Astelco
        self._tpl.set('TELESCOPE.STOP', 1, wait=True)
        return True

    @lock
    def getRa(self):  # converted to Astelco

        ret = self._tpl.getobject('POSITION.EQUATORIAL.RA_J2000')
        if ret:
			self._ra = Coord.fromH(ret)
        self.log.debug('Ra: %9.5f'%float(ret))
        return self._ra

    @lock
    def getDec(self):  # converted to Astelco
        ret = self._tpl.getobject('POSITION.EQUATORIAL.DEC_J2000')
        if ret:
			self._dec = Coord.fromD(ret)
        self.log.debug('Dec: %9.5f'%float(ret))
        return self._dec

    @lock
    def getPositionRaDec(self):  # no need to convert to Astelco
        return Position.fromRaDec(self.getRa(), self.getDec())

    @lock
    def getPositionAltAz(self):  # no need to convert to Astelco
        return Position.fromAltAz(self.getAlt(), self.getAz())

    @lock
    def getTargetRaDec(self):  # no need to convert to Astelco
        return Position.fromRaDec(self.getTargetRa(), self.getTargetDec())

    @lock
    def getTargetAltAz(self):  # no need to convert to Astelco
        return Position.fromAltAz(self.getTargetAlt(), self.getTargetAz())

    @lock
    def setTargetRaDec(self, ra, dec):  # no need to convert to Astelco
        self.setTargetRa(ra)
        self.setTargetDec(dec)

        return True

    @lock
    def setTargetAltAz(self, alt, az):  # no need to convert to Astelco
        self.setTargetAz(az)
        self.setTargetAlt(alt)

        return True

    @lock
    def getTargetRa(self):  # converted to Astelco
        ret = self._tpl.getobject('OBJECT.EQUATORIAL.RA')

        return Coord.fromH(ret)

    @lock
    def setTargetRa(self, ra):  # converted to Astelco
        if not isinstance(ra, Coord):
            ra = Coord.fromHMS(ra)

        cmdid = self._tpl.set('OBJECT.EQUATORIAL.RA', ra.H, wait=True)

        ret = self._tpl.succeeded(cmdid)

        if not ret:
            raise AstelcoException("Invalid RA '%s'" % ra)

        return True

    @lock
    def setTargetDec(self, dec):  # converted to Astelco
        if not isinstance(dec, Coord):
            dec = Coord.fromDMS(dec)

        cmdid = self._tpl.set('OBJECT.EQUATORIAL.DEC', dec.D, wait=True)

        ret = self._tpl.succeeded(cmdid)

        if not ret:
            raise AstelcoException("Invalid DEC '%s'" % dec)

        return True

    @lock
    def getTargetDec(self):  # converted to Astelco
        ret = self._tpl.getobject('OBJECT.EQUATORIAL.DEC')

        return Coord.fromD(ret)

    @lock
    def getAz(self):  # converted to Astelco
        ret = self._tpl.getobject('POSITION.HORIZONTAL.AZ')
        if ret:
			self._az = Coord.fromD(ret)
        self.log.debug('Az: %9.5f'%float(ret))
		
        c = self._az #Coord.fromD(ret)

        if self['azimuth180Correct']:
            if c.toD() >= 180:
                c = c - Coord.fromD(180)
            else:
                c = c + Coord.fromD(180)

        return c

    @lock
    def getAlt(self):  # converted to Astelco
        ret = self._tpl.getobject('POSITION.HORIZONTAL.ALT')
        if ret:
			self._alt = Coord.fromD(ret)
        self.log.debug('Alt: %9.5f'%float(ret))
		
        return self._alt

    def getTargetAlt(self):  # no need to convert to Astelco
        return self._target_alt

    @lock
    def setTargetAlt(self, alt):  # converted to Astelco
        if not isinstance(alt, Coord):
            alt = Coord.fromD(alt)

        cmdid = self._tpl.set('OBJECT.HORIZONTAL.ALT', alt.D, wait=True)

        ret = self._tpl.succeeded(cmdid)

        if not ret:
            raise AstelcoException("Invalid Altitude '%s'" % alt)

        self._target_alt = alt

        return True

    def getTargetAz(self):  # no need to convert to Astelco
        return self._target_az

    @lock
    def setTargetAz(self, az):  # converted to Astelco
        if not isinstance(az, Coord):
            az = Coord.fromDMS(az)

        if self['azimuth180Correct']:

            if az.toD() >= 180:
                az = az - Coord.fromD(180)
            else:
                az = az + Coord.fromD(180)

        cmdid = self._tpl.set('OBJECT.HORIZONTAL.AZ', az.D, wait=True)

        ret = self._tpl.succeeded(cmdid)

        if not ret:
            raise AstelcoException(
                "Invalid Azimuth '%s'" % az.strfcoord("%(d)03d\xdf%(m)02d"))

        self._target_az = az

        return True

    @lock
    def getLat(self):  # converted to Astelco
        ret = self._tpl.getobject('POINTING.SETUP.LOCAL.LATITUDE')

        return Coord.fromD(ret)

    @lock
    def setLat(self, lat):  # converted to Astelco
        if not isinstance(lat, Coord):
            lat = Coord.fromDMS(lat)

        lat_float = float(lat.D)

        cmdid = self._tpl.set(
            'POINTING.SETUP.LOCAL.LATITUDE', float(lat_float), wait=True)
        ret = self._tpl.succeeded(cmdid)
        if not ret:
            raise AstelcoException(
                "Invalid Latitude '%s' ('%s')" % (lat, lat_float))
        return True

    @lock
    def getLong(self):  # converted to Astelco
        ret = self._tpl.getobject('POINTING.SETUP.LOCAL.LONGITUDE')
        return Coord.fromD(ret)

    @lock
    def setLong(self, coord):  # converted to Astelco
        if not isinstance(coord, Coord):
            coord = Coord.fromDMS(coord)
        cmdid = self._tpl.set(
            'POINTING.SETUP.LOCAL.LONGITUDE', coord.D, wait=True)
        ret = self._tpl.succeeded(cmdid)
        if not ret:
            raise AstelcoException("Invalid Longitude '%s'" % coord.D)
        return True

    @lock
    def getDate(self):  # converted to Astelco
        timef = time.mktime(
            time.localtime(self._tpl.getobject('POSITION.LOCAL.UTC')))
        return dt.datetime.fromtimestamp(timef).date()

    @lock
    def setDate(self, date):  # converted to Astelco
        return True

    @lock
    def getLocalTime(self):  # converted to Astelco
        timef = time.mktime(
            time.localtime(self._tpl.getobject('POSITION.LOCAL.UTC')))
        return dt.datetime.fromtimestamp(timef).time()

    @lock
    def setLocalTime(self, local):  # converted to Astelco
        ret = True
        if not ret:
            raise AstelcoException("Invalid local time '%s'." % local)
        return True

    @lock
    def getLocalSiderealTime(self):  # converted to Astelco
        ret = self._tpl.getobject('POSITION.LOCAL.SIDEREAL')
        c = Coord.fromH(ret)
        return dt.datetime.time(c.HMS[1:-1])

    @lock
    def setLocalSiderealTime(self, local):  # converted to Astelco
        return True

    @lock
    def getUTCOffset(self):  # converted to Astelco
        return time.timezone/3600.0

    @lock
    def setUTCOffset(self, offset):  # converted to Astelco
        ret = True
        if not ret:
            raise AstelcoException("Invalid UTC offset '%s'." % offset)
        return True

    @lock
    def getCurrentTrackingRate(self):  # yet to convert to Astelco
        #self._write(":GT#")
        ret = False  # self._readline()
        if not ret:
            raise AstelcoException("Couldn't get the tracking rate")
        ret = float(ret[:-1])
        return ret

    @lock
    def setCurrentTrackingRate(self, trk):  # yet to convert to Astelco
        trk = "%02.1f" % trk
        if len(trk) == 3:
            trk = "0" + trk
        #self._write(":ST%s#" % trk)
        ret = False  # self._readbool()
        if not ret:
            raise AstelcoException("Invalid tracking rate '%s'." % trk)
        #self._write(":TM#")
        return ret

    @lock
    def startTracking(self):  # converted to Astelco
        cmdid = self._tpl.set('POINTING.TRACK', 1, wait=True)
        return self._tpl.succeeded(cmdid)

        if self.getAlignMode() in (AlignMode.POLAR, AlignMode.ALT_AZ):
            return True
        self.setAlignMode(self._lastAlignMode)
        return True

    @lock
    def stopTracking(self):  # converted to Astelco
        cmdid = self._tpl.set('POINTING.TRACK', 0, wait=True)
        return self._tpl.succeeded(cmdid)

        if self.getAlignMode() == AlignMode.LAND:
            return True
        self._lastAlignMode = self.getAlignMode()
        self.setAlignMode(AlignMode.LAND)
        return True

    def isTracking(self):  # converted to Astelco
        return self._tpl.getobject('POINTING.TRACK')

        if self.getAlignMode() != AlignMode.LAND:
            return True
        return False

    # -- ITelescopeSync implementation --
    @lock
    def syncRaDec(self, position):  # yet to convert to Astelco
        self.setTargetRaDec(position.ra, position.dec)
        #self._write(":CM#")
        ret = False  # self._readline ()
        if not ret:
            raise AstelcoException(
                "Error syncing on '%s' '%s'." % (position.ra, position.dec))
        self.syncComplete(self.getPositionRaDec())
        return True

    @lock
    def setSlewRate(self, rate):  # no need to convert to Astelco
        self._slewRate = rate
        return True

    def getSlewRate(self):  # no need to convert to Astelco
        return self._slewRate

    # -- park

    def getParkPosition(self):  # no need to convert to Astelco
        return Position.fromAltAz(self["park_position_alt"],
                                  self["park_position_az"])

    @lock
    def setParkPosition(self, position):  # no need to convert to Astelco
        self["park_position_az"], self["park_position_alt"] = position.D

        return True

    def isParked(self):  # (yes) -no- need to convert to Astelco
		self._parked = self._tpl.getobject('TELESCOPE.READY_STATE') == 0
		return self._parked

    def isOpen(self):  # (yes) -no- need to convert to Astelco
		self._open = self._tpl.getobject('AUXILIARY.COVER.REALPOS') == 1
		return self._open

    @lock
    def park(self):  # converted to Astelco
        if self.isParked():
            return True

        # 1. slew to park position FIXME: allow different park
        # positions and conversions from ra/dec -> az/alt

        site = self.getManager().getProxy("/Site/0")
        #self.slewToRaDec(Position.fromRaDec(str(self.getLocalSiderealTime()),
#                                            site["latitude"]))
        cmdid = self._tpl.set('TELESCOPE.READY', 0, wait=True)

        ready_state = self._tpl.getobject('TELESCOPE.READY_STATE')
        while ready_state > 0.0:
            self.log.debug("Powering down Astelco: %s"%(ready_state))
            old_ready_state = ready_state
            ready_state = self._tpl.getobject('TELESCOPE.READY_STATE')
            if ready_state != old_ready_state:
                self.log.debug("Powering down Astelco: %s"%(ready_state))
                old_ready_state = ready_state
            time.sleep(5.0)

        # 2. stop tracking
        #self.stopTracking ()
        # 3. power off
        #self.powerOff ()
        self._parked = True

        self.parkComplete()

        return self._tpl.succeeded(cmdid)

    @lock
    def unpark(self):  # converted to Astelco

        if not self.isParked():
            return True
        # 1. power on
        #self.powerOn ()
        cmdid = self._tpl.set('TELESCOPE.READY', 1, wait=True)

        # 2. start tracking
        #self.startTracking()
        ready_state = 0.0
        while ready_state < 1.0:
            self.log.debug("Powering up Astelco: %s"%(ready_state))
            old_ready_state = ready_state
            ready_state = self._tpl.getobject('TELESCOPE.READY_STATE')
            if ready_state != old_ready_state:
                self.log.debug("Powering up Astelco: %s"%(ready_state))
                old_ready_state = ready_state
            time.sleep(5.0)

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
        return self._tpl.succeeded(cmdid)

    @lock
    def openCover(self):
		if self.isOpen():
			return True

		cmdid = self._tpl.set('AUXILIARY.COVER.TARGETPOS', 1, wait=True)

		self.log.debug('Opening telescope cover...')

		ready_state = 0.0
		while ready_state < 1.0:
			self.log.debug("Opening telescope cover: %s"%(ready_state))
			#old_ready_state = ready_state
			ready_state = self._tpl.getobject('AUXILIARY.COVER.REALPOS')
			#if ready_state != old_ready_state:
			#    self.log.debug("Powering up Astelco: %s"%(ready_state))
			#    old_ready_state = ready_state
			time.sleep(5.0)


		return self._tpl.succeeded(cmdid)

    @lock
    def closeCover(self):
		if not self.isOpen():
			return True
			
		self.log.debug('Closing telescope cover...')

		cmdid = self._tpl.set('AUXILIARY.COVER.TARGETPOS', 0, wait=True)

		ready_state = 1.0
		while ready_state > 0.0:
			self.log.debug("Closing telescope cover: %s"%(ready_state))
			#old_ready_state = ready_state
			ready_state = self._tpl.getobject('AUXILIARY.COVER.REALPOS')
			#if ready_state != old_ready_state:
			#    self.log.debug("Powering up Astelco: %s"%(ready_state))
			#    old_ready_state = ready_state
			time.sleep(5.0)

		return True #self._tpl.succeeded(cmdid)

    # low-level
    def _debug(self, msg):  # no need to convert to Astelco
        if self._debugLog:
            print >> self._debugLog, time.time(), threading.currentThread().getName(), msg
            self._debugLog.flush()

    def _read(self, n=1, flush=True):  # not used for Astelco
        if not self._tty.isOpen():
            raise IOError("Device not open")

        if flush:
            self._tty.flushInput()

        ret = self._tty.read(n)
        self._debug("[read ] %s" % repr(ret))
        return ret

    def _readline(self, eol='#'):  # not used for Astelco
        if not self._tty.isOpen():
            raise IOError("Device not open")

        ret = self._tty.readline(None, eol)
        self._debug("[read ] %s" % repr(ret))
        return ret

    def _readbool(self):  # not used for Astelco
        try:
            ret = int(self._read(1))
        except ValueError:
            return False

        if not ret:
            return False

        return True

    def _write(self, data, flush=True):  # not used for Astelco
        if not self._tty.isOpen():
            raise IOError("Device not open")

        if flush:
            self._tty.flushOutput()

        self._debug("[write] %s" % repr(data))

        return self._tty.write(data)

    def getobject(self, object):
        return self._tpl.getobject(object)

    def set(self, object, value, wait=False, binary=False):
        return self._tpl.set(object, value, wait=False, binary=False)

    def getcommands_sent(self):
        return self._tpl.commands_sent

    def getlog(self):
        return self._tpl.log

