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
# from types import FloatType
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

from chimera.util.tpl2 import TPL2, SocketError


Direction = Enum("E", "W", "N", "S")
AstelcoTelescopeStatus = Enum("NoLICENSE",
                              "NoTELESCOPE",
                              "OK",
                              "PANIC",
                              "ERROR",
                              "WARNING",
                              "INFO")


class AstelcoException(ChimeraException):
    pass


class Astelco(TelescopeBase):  # converted to Astelco

    __config__ = {'azimuth180Correct': False,
                  'user': 'admin',
                  'password': 'admin',
                  'ahost': 'localhost',
                  'aport': '65432',
                  'maxidletime': 90.,
                  'parktimeout': 600.,
                  'tplsleep': 0.01,
                  'sensors': 7}  # TODO: FIX tpl so I can get COUNT on an axis.


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

        self.setHz(1. / self["maxidletime"])

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

    @lock
    def open(self):  # converted to Astelco
        self.log.info('Connecting to Astelco server %s:%i' % (self["ahost"],
                                                              int(self["aport"])))

        self._tpl = TPL2(user=self["user"],
                         password=self["password"],
                         host=self["ahost"],
                         port=int(self["aport"]),
                         echo=False,
                         verbose=False,
                         sleep=self["tplsleep"],
                         debug=False)

        self.log.debug(self._tpl.log)

        try:
            self._tpl  #.open()

            self._checkAstelco()

            #if self["auto_align"]:
            #    self.autoAlign ()

            # manualy initialize scope
            if self["skip_init"]:
                self.log.info("Skipping init as requested.")
            else:
                self._initTelescope()

            return True

        except (SocketError, IOError):
            raise AstelcoException("Error while opening %s." % self["device"])

    @lock
    def control(self):
        '''
        Check for telescope status and try to acknowledge any event. This also
        keeps the connection alive.

        :return: True
        '''

        #self.log.debug('[control] %s'%self._tpl.getobject('SERVER.UPTIME'))

        status = self.getTelescopeStatus()

        if status == AstelcoTelescopeStatus.OK:
            self.log.debug('[control] Status: %s' % status)
            return True
        elif status == AstelcoTelescopeStatus.WARNING or status == AstelcoTelescopeStatus.INFO:
            self.log.info('[control] Got telescope status "%s", trying to acknowledge it... ' % status)
            self.acknowledgeEvents()
        elif status == AstelcoTelescopeStatus.PANIC or status == AstelcoTelescopeStatus.ERROR:
            self.log.error('[control] Telescope in %s mode! Cannot operate!' % status)
            # What should be done? Try to acknowledge and if that fails do what?
        else:
            return False

        return True

    @lock
    def close(self):  # converted to Astelco
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
        except Exception, e:
            self._slewing = False
            if self._abort.isSet():
                status = TelescopeStatus.ABORTED
            else:
                status = TelescopeStatus.ERROR
            self.slewComplete(self.getPositionRaDec(), status)
            self.log.exception(e)
        finally:
            self._slewing = False
            self.slewComplete(self.getPositionRaDec(), status)
            return status


    def _slewToRaDec(self):  # converted to Astelco
        self._slewing = True
        self._abort.clear()

        # slew
        slewTime = self._tpl.getobject('POINTING.SLEWTIME')
        self.log.info("Time to slew to RA/Dec is reported to be %f s" % ( slewTime ))

        target = self.getTargetRaDec()

        return self._waitSlew(time.time(), target, slew_time=slewTime)

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
        except Exception, e:
            self._slewing = False
            status = TelescopeStatus.ERROR
            if self._abort.isSet():
                status = TelescopeStatus.ABORTED
        finally:
            self.slewComplete(self.getPositionRaDec(), status)
            self.setAlignMode(lastAlignMode)
            return status

    def _slewToAltAz(self):  # converted to Astelco
        self._slewing = True
        self._abort.clear()

        # slew
        self.log.debug("Time to slew to Alt/Az is reported to be %s s." % self._tpl.getobject('POINTING.SLEWTIME'))

        target = self.getTargetAltAz()

        return self._waitSlew(time.time(), target, local=True)

    def _waitSlew(self, start_time, target, local=False, slew_time=-1):  # converted to Astelco
        self.slewBegin(target)

        # Set offset to zero
        if abs(self._getOffset(Direction.N)) > 0:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.DEC.OFFSET', 0.0, wait=True)
            time.sleep(self["stabilization_time"])
        if abs(self._getOffset(Direction.W)) > 0:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.HA.OFFSET', 0.0, wait=True)
            time.sleep(self["stabilization_time"])

        self.log.debug('SEND: POINTING.TRACK 2')
        cmdid = self._tpl.set('POINTING.TRACK', 2, wait=True)
        self.log.debug('PASSED')

        err = not self._tpl.succeeded(cmdid)

        if err:
            # check error message
            msg = self._tpl.commands_sent[cmdid]['received']
            self.log.error('Error pointing to %s' % target)
            for line in msg:
                self.log.error(line[:-1])
            self.slewComplete(self.getPositionRaDec(),
                TelescopeStatus.ERROR)

            return TelescopeStatus.ERROR

        self.log.debug('Wait cmd complete...')
        status = self.waitCmd(cmdid, start_time, slew_time)
        self.log.debug('Done')

        if status != TelescopeStatus.OK:
            self.log.warning('Pointing operations failed with status: %s...' % status)
            self.slewComplete(self.getPositionRaDec(),
                status)
            return status

        self.log.debug('Wait movement start...')
        time.sleep(self["stabilization_time"])

        self.log.debug('Wait slew to complete...')

        while True:

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

            if time.time() >= (start_time + slew_time):
                self.log.warning('Estimated slewtime has passed...')
                position = self.getPositionRaDec()
                if local:
                    position = self.getPositionAltAz()
                angsep = target.angsep(position)
                self.log.debug('Target: %s | Position: %s | Distance: %s' % (target, position, angsep))

                slew_time += slew_time

            mstate = self._tpl.getobject('TELESCOPE.MOTION_STATE')

            self.log.debug('MSTATE: %i (%s)' % (mstate, bin(mstate)))
            if (mstate & 1) == 0:
                self.log.debug('Slew finished...')
                break

            time.sleep(self["slew_idle_time"])

        self.log.debug('SEND: POINTING.TRACK 1')
        cmdid = self._tpl.set('POINTING.TRACK', 1, wait=True)
        self.log.debug('PASSED')

        self.log.debug('Wait for telescope to stabilize...')
        time.sleep(self["stabilization_time"])

        self.log.debug('Wait cmd complete...')
        status = self.waitCmd(cmdid, start_time, slew_time)
        self.log.debug('Done')

        self.log.debug('Wait slew to complete...')

        time.sleep(self["slew_idle_time"])

        while self._isSlewing():

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

            if time.time() >= (start_time + slew_time):
                self.log.warning('Estimated slewtime has passed...')
                slew_time += slew_time

            time.sleep(self["slew_idle_time"])

        self.log.debug('Wait for telescope to stabilize...')
        time.sleep(self["stabilization_time"])

        # no need to check it here...
        return status


    def waitCmd(self, cmdid, start_time, op_time=-1):

        if op_time < 0:
            op_time = self["max_slew_time"] + 1

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
                op_time += op_time

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

        return self._isSlewing()

    def _isSlewing(self):

        self.log.debug('GET TELESCOPE.MOTION_STATE')
        mstate = self._tpl.getobject('TELESCOPE.MOTION_STATE')
        self.log.debug('GET POINTING.TRACK')
        ptrack = self._tpl.getobject('POINTING.TRACK')
        self.log.debug('Done')

        self._slewing = (int(mstate) != 0) and (int(ptrack) != 1)

        return self._slewing

    def _getOffset(self, direction):

        if direction == Direction.E or direction == Direction.W:
            return self._tpl.getobject('POSITION.INSTRUMENTAL.HA.OFFSET')
        elif direction == Direction.N or direction == Direction.S:
            return self._tpl.getobject('POSITION.INSTRUMENTAL.DEC.OFFSET')
        else:
            return 0

    def _move(self, direction, offset, slewRate=SlewRate.GUIDE):  # yet to convert to Astelco

        current_offset = self._getOffset(direction)

        self._slewing = True
        cmdid = 0

        self.log.debug('Current offset: %s | Requested: %s' % (current_offset, offset / 60. / 60.))

        if direction == Direction.W:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.HA.OFFSET', current_offset + offset / 60. / 60., wait=True)
        elif direction == Direction.E:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.HA.OFFSET', current_offset - offset / 60. / 60., wait=True)
        elif direction == Direction.N:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.DEC.OFFSET', current_offset + offset / 60. / 60., wait=True)
        elif direction == Direction.S:
            cmdid = self._tpl.set('POSITION.INSTRUMENTAL.DEC.OFFSET', current_offset - offset / 60. / 60., wait=True)
        else:
            return True

        self.log.debug('Wait for telescope to stabilize...')
        time.sleep(self["stabilization_time"])

        self.log.debug('Wait cmd complete...')
        start_time = time.time()
        slew_time = self["stabilization_time"]
        status = self.waitCmd(cmdid, start_time, slew_time)

        self.log.debug('SEND: POINTING.TRACK 1')
        cmdid = self._tpl.set('POINTING.TRACK', 1, wait=True)
        self.log.debug('PASSED')

        self.log.debug('Wait for telescope to stabilize...')
        time.sleep(self["stabilization_time"])

        self.log.debug('Wait cmd complete...')
        status = self.waitCmd(cmdid, start_time, slew_time)
        self.log.debug('Done')

        self.log.debug('Wait slew to complete...')

        time.sleep(self["slew_idle_time"])

        while self._isSlewing():

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

            if time.time() >= (start_time + slew_time):
                self.log.warning('Estimated slewtime has passed...')
                slew_time += slew_time

            time.sleep(self["slew_idle_time"])

        self.log.debug('Wait for telescope to stabilize...')
        time.sleep(self["stabilization_time"])

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

                self.log.debug("> %f" % (total / 2.0))
                self._calibration[rate][direction] = total / 2.0

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

        return arc * (self._calibration_time / self._calibration[rate][direction])

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
        self.log.debug('Ra: %s' % ret)
        return self._ra

    @lock
    def getDec(self):  # converted to Astelco
        ret = self._tpl.getobject('POSITION.EQUATORIAL.DEC_J2000')
        if ret:
            self._dec = Coord.fromD(ret)
        self.log.debug('Dec: %s' % ret)
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
        self.log.debug('Az: %s' % ret)

        c = self._az  #Coord.fromD(ret)

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
        self.log.debug('Alt: %s' % ret)

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
        return time.timezone / 3600.0

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


    @lock
    def stopTracking(self):  # converted to Astelco
        cmdid = self._tpl.set('POINTING.TRACK', 0, wait=True)
        return self._tpl.succeeded(cmdid)


    def isTracking(self):  # converted to Astelco
        return self._tpl.getobject('POINTING.TRACK')


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
        start_time = time.time()
        self._abort.clear()

        while ready_state > 0.0:
            self.log.debug("Powering down Astelco: %s" % (ready_state))
            old_ready_state = ready_state
            ready_state = self._tpl.getobject('TELESCOPE.READY_STATE')
            if ready_state != old_ready_state:
                self.log.debug("Powering down Astelco: %s" % (ready_state))
                old_ready_state = ready_state
            if self._abort.set():
                # Send abork command to astelco
                self.log.warning("Abort parking! This will leave the telescope in an intermediate state!")
                self._tpl.set('ABORT', cmdid)
                return False
            if time.time() > start_time + self['parktimeout']:
                self.log.error("Parking operation timedout!")
                return False
            if self.getTelescopeStatus() != AstelcoTelescopeStatus.OK:
                self.log.warning("Something wrong with telescope! Trying to fix it!")
                self.logStatus()
                self.acknowledgeEvents()
                # What should I do if acknowledging events does not fix it?

            time.sleep(5.0)

        # 2. stop tracking
        #self.stopTracking ()
        # 3. power off
        #self.powerOff ()
        self._parked = True

        self.parkComplete()

        return self._tpl.succeeded(cmdid)

    def getTelescopeStatus(self):
        '''
        Get telescope status.
        -2 - No valid license found
        -1 - No Telescope hardware found
        0 - Operational
        Bit 0 - PANIC, a severe condition, completely disabling the entire telescope,
        Bit 1 - ERROR, a serious condition, disabling important parts of the telescope system,
        Bit 2 - WARNING, a critical condition, which is not (yet) dis- abling the telescope,
        Bit 3 - INFO, a informal situation, which is not a ecting the operation.

        :return: AstelcoTelescopeStatus{Enum}
        '''
        status = self._tpl.getobject('TELESCOPE.STATUS.GLOBAL')

        if status == 0:
            return AstelcoTelescopeStatus.OK
        elif status == -2:
            return AstelcoTelescopeStatus.NoLICENSE
        elif status == -1:
            return AstelcoTelescopeStatus.NoTELESCOPE
        elif (status & ( 1 << 0 ) ) != 0:
            # Bit 0 is set! PANIC!
            return AstelcoTelescopeStatus.PANIC
        elif (status & ( 1 << 1 ) ) != 0:
            return AstelcoTelescopeStatus.ERROR
        elif (status & ( 1 << 2 ) ) != 0:
            return AstelcoTelescopeStatus.WARNING
        elif (status & ( 1 << 3 ) ) != 0:
            return AstelcoTelescopeStatus.INFO

        return AstelcoTelescopeStatus.OK

    def logStatus(self):
        # ToDo: Get Status message and log
        pass

    def acknowledgeEvents(self):
        '''
        Try to resolve any issue with the telescope by acknowledging its existence. This may
        resolve most of the common issues. Depending on the severity, the telescope may be
        in an error state even after acknowledging.

        :return: True  - acknowledge registered
                 False - acknowledge ignored
        '''

        # Get GLOBAL STATUS
        status = self._tpl.getobject('TELESCOPE.STATUS.GLOBAL')
        if status > 0:
            self.log.debug("Telescope status not OK... Trying to acknowledge...")
            # writing GLOBAL status to CLEAR is how you acknowledge
            cmdid = self._tpl.set('TELESCOPE.STATUS.CLEAR', status)
            # if clear gets new value, acknowledge may have worked
            self.waitCmd(cmdid, time.time(), self["maxidletime"])
            #clear = self._tpl.getobject('TELESCOPE.STATUS.CLEAR')
            #if clear == status:
            #    self.log.debug("CLEAR accepted new value...")
            # I will go ahead and check status anyway...
            # if GLOBAL is zero, than acknowledge worked
            status = self._tpl.getobject('TELESCOPE.STATUS.GLOBAL')
            if status == 0:
                self.log.debug('Acknowledge accepted...')
                return True
            else:
                self.log.warning('Acknowledge refused...')
                return False
        else:
            self.log.debug('Telescope status OK...')
            return True

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
        start_time = time.time()
        self._abort.clear()

        while ready_state < 1.0:
            self.log.debug("Powering up Astelco: %s" % (ready_state))
            old_ready_state = ready_state
            ready_state = self._tpl.getobject('TELESCOPE.READY_STATE')

            if ready_state != old_ready_state:
                self.log.debug("Powering up Astelco: %s" % (ready_state))
                old_ready_state = ready_state
            if self._abort.set():
                # Send abort command to astelco
                self.log.warning("Abort parking! This will leave the telescope in an intermediate state!")
                self._tpl.set('ABORT', cmdid)
                return False
            if time.time() > start_time + self['parktimeout']:
                self.log.error("Parking operation timedout!")
                self._tpl.set('ABORT', cmdid)
                raise AstelcoException('Unparking telescope aborted. TIMEOUT.')

            status = self.getTelescopeStatus()
            if status == AstelcoTelescopeStatus.WARNING or status == AstelcoTelescopeStatus.INFO:
                self.log.warning("Acknowledging telescope state.")
                self.logStatus()
                self.acknowledgeEvents() # This is needed so I can tell the telescope to park
            elif status == AstelcoTelescopeStatus.ERROR or status == AstelcoTelescopeStatus.PANIC:
                # When something really bad happens during unpark, telescope needs to be parked
                # and then, start over.
                self._tpl.set('ABORT', cmdid)
                self.log.critical("Something wrong with the telescope. Acknowledging state and aborting...")
                self.logStatus()
                self.acknowledgeEvents() # This is needed so I can tell the telescope to park afterwards
                errmsg = '''Something wrong happened while trying to unpark the telescope. In most cases this happens
                when one of the submodules (like the hexapod) is not properly loaded. Waiting a couple of minutes,
                parking and unparking it again should solve the problem. If that doesn't work, there may be a more
                serious problem with the system.'''
                raise AstelcoException(errmsg)

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
            self.log.debug("Opening telescope cover: %s" % (ready_state))
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
            self.log.debug("Closing telescope cover: %s" % (ready_state))
            #old_ready_state = ready_state
            ready_state = self._tpl.getobject('AUXILIARY.COVER.REALPOS')
            #if ready_state != old_ready_state:
            #    self.log.debug("Powering up Astelco: %s"%(ready_state))
            #    old_ready_state = ready_state
            time.sleep(5.0)

        return True  #self._tpl.succeeded(cmdid)

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

    def getSensors(self):

        sensors = []

        for n in range(self["sensors"]):
            description = self._tpl.getobject('AUXILIARY.SENSOR[%i].DESCRIPTION' % (n + 1))
            if not description:
                continue
            elif "FAILED" in description:
                continue
            value = self._tpl.getobject('AUXILIARY.SENSOR[%i].VALUE' % (n + 1))
            unit = self._tpl.getobject('AUXILIARY.SENSOR[%i].UNITY' % (n + 1))
            sensors.append((description, value, unit))

        return sensors

    def getMetadata(self, request):
        return [('TELESCOP', self['model'], 'Telescope Model'),
                ('OPTICS', self['optics'], 'Telescope Optics Type'),
                ('MOUNT', self['mount'], 'Telescope Mount Type'),
                ('APERTURE', self['aperture'], 'Telescope aperture size [mm]'),
                ('F_LENGTH', self['focal_length'],
                 'Telescope focal length [mm]'),
                ('F_REDUCT', self['focal_reduction'],
                 'Telescope focal reduction'),
                # TODO: Convert coordinates to proper equinox
                # TODO: How to get ra,dec at start of exposure (not end)
                ('RA', self.getRa().toHMS().__str__(),
                 'Right ascension of the observed object'),
                ('DEC', self.getDec().toDMS().__str__(),
                 'Declination of the observed object'),
                ("EQUINOX", 2000.0, "coordinate epoch"),
                ('ALT', self.getAlt().toDMS().__str__(),
                 'Altitude of the observed object'),
                ('AZ', self.getAz().toDMS().__str__(),
                 'Azimuth of the observed object'),
                ("WCSAXES", 2, "wcs dimensionality"),
                ("RADESYS", "ICRS", "frame of reference"),
                ("CRVAL1", self.getTargetRaDec().ra.D,
                 "coordinate system value at reference pixel"),
                ("CRVAL2", self.getTargetRaDec().dec.D,
                 "coordinate system value at reference pixel"),
                ("CTYPE1", 'RA---TAN', "name of the coordinate axis"),
                ("CTYPE2", 'DEC---TAN', "name of the coordinate axis"),
                ("CUNIT1", 'deg', "units of coordinate value"),
                ("CUNIT2", 'deg', "units of coordinate value")] + self.getSensors()
