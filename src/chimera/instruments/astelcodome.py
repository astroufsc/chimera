#! /usr/bin/env python
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

import os
import time
import threading

from chimera.util.coord import Coord

from chimera.interfaces.dome import DomeStatus
from chimera.instruments.dome import DomeBase
from chimera.interfaces.dome import Mode

from chimera.core.lock import lock
from chimera.core.exceptions import ChimeraException
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.util.tpl2 import TPL2, SocketError


class AstelcoException(ChimeraException):
    pass


class AstelcoDomeException(ChimeraException):
    pass


class AstelcoDome(DomeBase):
    '''
    AstelcoDome interfaces chimera with TSI system to control dome.
    '''

    __config__ = {'user': 'admin',
                  'password': 'admin',
                  'ahost': 'localhost',
                  'aport': "65432",
                  "maxidletime": 90.,
                  "stabilization_time": 5.}


    def __init__(self):
        DomeBase.__init__(self)

        self._position = 0
        self._slewing = False
        self._maxSlewTime = 300.

        self._syncmode = 0

        self._slitOpen = False
        self._slitMoving = False

        self._abort = threading.Event()

        self._errorNo = 0

        self._errorString = ""

        # debug log
        self._debugLog = None

        try:
            self._debugLog = open(os.path.join(SYSTEM_CONFIG_DIRECTORY,
                                               "astelcodome-debug.log"), "w")
        except IOError, e:
            self.log.warning("Could not create astelco debug file (%s)" % str(e))


    def __start__(self):

        self.setHz(1. / self["maxidletime"])

        self.open()

        # Reading position
        self._position = self._tpl.getobject('POSITION.HORIZONTAL.DOME')
        self._slitOpen = self._tpl.getobject('AUXILIARY.DOME.REALPOS') > 0
        self._slitPos = self._tpl.getobject('AUXILIARY.DOME.REALPOS')
        self._syncmode = self._tpl.getobject('POINTING.SETUP.DOME.SYNCMODE')
        self._tel = self.getTelescope()

        if self._syncmode == 0:
            self._mode = Mode.Stand
        else:
            self._mode = Mode.Track

        return True

    def __stop__(self):  # converted to Astelco
        if self.isSlewing():
            self.abortSlew()

        self.close()

    @lock
    def slewToAz(self, az):
        # Astelco Dome will only enable slew if it is not tracking
        # If told to slew I will check if the dome is syncronized with
        # with the telescope. If it is not I will wait until it gets
        # in sync or timeout...

        if self._mode == Mode.Track:
            self.log.warning('Dome is in track mode... Slew is completely controled by AsTelOS...')
            self.slewBegin(az)

            start_time = time.time()
            self._abort.clear()
            self._slewing = True
            caz = self.getAz()

            while self.isSlewing():
                time.sleep(1.0)
                if time.time() > (start_time + self._maxSlewTime):
                    self.log.warning('Dome syncronization timed-out...')
                    self.slewComplete(self.getAz(), DomeStatus.TIMEOUT)
                    return 0
                elif self._abort.isSet():
                    self._slewing = False
                    self.slewComplete(self.getAz(), DomeStatus.ABORTED)
                    return 0
                elif abs(caz - self.getAz()) < 1e-6:
                    self._slewing = False
                    self.slewComplete(self.getAz(), DomeStatus.OK)
                    return 0
                else:
                    caz = self.getAz()

            self.slewComplete(self.getAz(), DomeStatus.OK)
        else:
            self.log.info('Slewing to %f...' % az)

            self.slewBegin(az)

            start_time = time.time()
            self._abort.clear()
            self._slewing = True
            caz = self.getAz()

            self._tpl.set('POSITION.INSTRUMENTAL.DOME[0].TARGETPOS', '%f' % az)

            time.sleep(self['stabilization_time'])

            while self.isSlewing():
                time.sleep(1.0)
                if time.time() > (start_time + self._maxSlewTime):
                    self.log.warning('Dome syncronization timed-out...')
                    self.slewComplete(self.getAz(), DomeStatus.TIMEOUT)
                    return 0
                elif self._abort.isSet():
                    self._slewing = False
                    self._tpl.set('POSITION.INSTRUMENTAL.DOME[0].TARGETPOS', caz)
                    self.slewComplete(self.getAz(), DomeStatus.ABORTED)
                    return 0
                elif abs(caz - self.getAz()) < 1e-6:
                    self._slewing = False
                    self.slewComplete(self.getAz(), DomeStatus.OK)
                    return 0
                else:
                    caz = self.getAz()

            self.slewComplete(self.getAz(), DomeStatus.OK)

            raise NotImplementedError('Dome slew not implemented...')


    @lock
    def stand(self):
        self.log.debug("[mode] standing...")
        self._tpl.set('POINTING.SETUP.DOME.SYNCMODE', 0)
        self._syncmode = self._tpl.getobject('POINTING.SETUP.DOME.SYNCMODE')
        self._mode = Mode.Stand

    @lock
    def track(self):
        self.log.debug("[mode] tracking...")
        self._tpl.set('POINTING.SETUP.DOME.SYNCMODE', 4)
        self._syncmode = self._tpl.getobject('POINTING.SETUP.DOME.SYNCMODE')
        self._mode = Mode.Track

    @lock
    def control(self):
        '''
        Just keep the connection alive. Everything else is done by astelco.

        :return: True
        '''

        self.log.debug('[control] %s' % self._tpl.getobject('SERVER.UPTIME'))

        return True


    def isSlewing(self):

        motionState = self._tpl.getobject('TELESCOPE.MOTION_STATE')
        return ( motionState != 11 )

    def abortSlew(self):
        self._abort.set()

    @lock
    def getAz(self):

        ret = self._tpl.getobject('POSITION.INSTRUMENTAL.DOME[0].CURRPOS')
        if ret:
            self._position = ret
        elif not self._position:
            self._position = 0.

        return Coord.fromD(self._position)

    def getMode(self):

        self._syncmode = self._tpl.getobject('POINTING.SETUP.DOME.SYNCMODE')

        if self._syncmode == 0:
            self._mode = Mode.Stand
        else:
            self._mode = Mode.Track
        return self._mode

    @lock
    def open(self):
        self.log.info('Connecting to Astelco server %s:%i...' % (self['ahost'], int(self['aport'])))

        self._tpl = TPL2(user=self['user'],
                         password=self['password'],
                         host=self['ahost'],
                         port=int(self['aport']),
                         echo=False,
                         verbose=False,
                         debug=True)

        self.log.debug(self._tpl.log)

        try:
            self._tpl.get('SERVER.INFO.DEVICE')
            print self._tpl.getobject('SERVER.UPTIME')
            self._tpl.debug = True
            return True

        except (SocketError, IOError):
            raise AstelcoException("Error while opening %s." % self["device"])

    @lock
    def close(self):  # converted to Astelco
        if self._tpl.isListening():
            self._tpl.disconnect()
            return True
        else:
            return False


    @lock
    def openSlit(self):

        # check slit condition

        if self._slitMoving:
            raise AstelcoException('Slit already opening...')
        elif self._slitOpen:
            self.log.info('Slit already opened...')
            return 0

        self._slitMoving = True
        self._abort.clear()

        cmdid = self._tpl.set('AUXILIARY.DOME.TARGETPOS', 1, wait=True)

        time_start = time.time()

        cmdComplete = False
        while True:

            realpos = self._tpl.getobject('AUXILIARY.DOME.REALPOS')

            for line in self._tpl.commands_sent[cmdid]['received']:
                self.log.info(line[:-1])
                if ( (line.find('COMPLETE') > 0) and (not realpos == 1) and (not cmdComplete) ):
                    self.log.warning('Slit opened! Opening Flap...')
                    cmdid = self._tpl.set('AUXILIARY.DOME.TARGETPOS', 1, wait=True)
                    cmdComplete = True
                    time_start = time.time()

            if realpos == 1:
                self._slitMoving = False
                self._slitOpen = True
                return DomeStatus.OK
            elif self._abort.isSet():
                self._slitMoving = False
                return DomeStatus.ABORTED
            elif time.time() > time_start + self._maxSlewTime:
                return DomeStatus.TIMEOUT
            else:
                time.sleep(5.0)

        return True

    @lock
    def closeSlit(self):
        if not self._slitOpen:
            self.log.info('Slit already closed')
            return 0

        self.log.info("Closing slit")

        cmdid = self._tpl.set('AUXILIARY.DOME.TARGETPOS', 0)

        time_start = time.time()

        while True:

            for line in self._tpl.commands_sent[cmdid]['received']:
                self.log.info(line[:-1])

            realpos = self._tpl.getobject('AUXILIARY.DOME.REALPOS')
            if realpos == 0:
                self._slitMoving = False
                self._slitOpen = False
                return DomeStatus.OK
            elif self._abort.isSet():
                self._slitMoving = False
                return DomeStatus.ABORTED
            elif time.time() > time_start + self._maxSlewTime:
                return DomeStatus.TIMEOUT
            else:
                time.sleep(5.0)


    def isSlitOpen(self):
        self._slitPos = self._tpl.getobject('AUXILIARY.DOME.REALPOS')
        self._slitOpen = self._slitPos > 0
        return self._slitOpen
