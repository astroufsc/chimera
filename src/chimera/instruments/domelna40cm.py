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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import time
import serial
import threading
import math
import os
import select

from chimera.instruments.dome import DomeBase
from chimera.interfaces.dome  import InvalidDomePositionException

from chimera.core.exceptions import ChimeraException
from chimera.core.lock import lock
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.util.coord import Coord


class DomeLNA40cm (DomeBase):

    def __init__(self):
        DomeBase.__init__ (self)

        self.tty = None
        self.abort = threading.Event ()

        self._slewing  = False
        self._slitOpen = False

        self._az_shift = 0

        self._num_restarts = 0
        self._max_restarts = 3

        # debug log
        self._debugLog = None
        try:
            self._debugLog = open(os.path.join(SYSTEM_CONFIG_DIRECTORY, "dome-debug.log"), "w")
        except IOError, e:
            self.log.warning("Could not create meade debug file (%s)" % str(e))

    def __start__ (self):

        # NOTE: DomeBase __start__ expect the serial port to be open, so open it before
        #       calling super().__start__.

        try:
            self.open()
        except Exception, e:
            self.log.exception(e)
            return False

        return super(DomeLNA40cm, self).__start__()

    def __stop__ (self):

        # NOTE: Here is the opposite, call super first and then close

        ret = super(DomeLNA40cm, self).__start__()
        if not ret: return ret

        self.close()

        return True

    def _checkDome (self):
        # just for test, ask azimuth
        self.getAz()
        return True

    def _checkQuirk (self):
        # clear uC command buffer sending and \r, this makes the uC happy!
        self._write("")

        ret = self._readline ()
        if ret != "INVALIDO":
            self.log.warning("Quirk error, restarting Dome.")
            self._restartDome()

        return True

    def _restartDome (self):

        if self._num_restarts >= self._max_restarts:
            raise ChimeraException("Could not restart the dome after %s tries. Manual restart needed." % self._max_restarts)
        else:
            self._num_restarts += 1
                                  

        self.log.info("Trying to restart the Dome.")

        self._write("INICIAR")

        ack = self._readline()
        if not ack == "INICIANDO":
            if not self._checkQuirk():
                raise ChimeraException("Could not restart dome! Manual restart needed.")
            else:
                self._num_restarts = 0
                return True

        ack2 = self._readline()
        if not ack2.startswith("CUPULA=") or ack2.startswith("CUPULA=ERRO") or ack == '':
            if not self._checkQuirk():
                raise ChimeraException("Could not restart dome! Manual restart needed.")
            else:
                self._num_restarts = 0
                return True

        self._num_restarts = 0

        return True

    @lock
    def open (self):

        self.tty = serial.Serial(self["device"], baudrate=9600,
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=self["init_timeout"],
                                 xonxoff=0, rtscts=0)


        self.tty.open()
        self.tty.flushInput ()
        self.tty.flushOutput ()

        self._checkDome()

    @lock
    def close(self):
        if self.tty.isOpen():
            self.tty.close()

    @lock
    def slewToAz(self, az):

        self._checkQuirk()

        # correct dome/telescope phase difference
        dome_az = az.D + self._az_shift

        if dome_az > 360:
            raise InvalidDomePositionException("Cannot slew to %s. "
                                               "Outside azimuth limits." % az)
        
        dome_az = int (math.ceil (dome_az / self["az_resolution"]))

        pstn = "CUPULA=%03d" % dome_az

        self.tty.setTimeout (self["slew_timeout"])

        self._write(pstn)

        ack = self._readline ()

        if ack == "INVALIDO":
            raise IOError("Error trying to slew the dome to"
                          "azimuth '%s' (dome azimuth '%s')." % (az, dome_az))

        # ok, we are slewing now
        self._slewing = True
        self.slewBegin(az)

        # FIXME: add abort option here
        fin = self._readline ()

        if fin == "ALARME":
            self.log.warning("Error while slewing dome. Some barcodes"
                             " couldn't be read correctly."
                             " Restarting the dome and trying again.")
            self._restartDome()
            return self.slewToAz(az)

        if fin.startswith ("CUPULA="):
            self._slewing = False
            time.sleep (0.3) # FIXME: how much sleep we need?
            self.slewComplete(self.getAz())
        else:
            self._slewing = False
            self.log.warning("Unknow error while slewing. "
                             "Received '%s' from dome. Restarting it." % fin)
            self._restartDome()
            return self.slewToAz(az)
          

    def isSlewing (self):
        return self._slewing

    def abortSlew(self):
        # FIXME: make abort work

        if not self.isSlewing(): return

        self._checkQuirk ()

        self._write("PARAR")

        self.tty.setTimeout (self["abort_timeout"])
        ack = self._readline ()

        if ack != "PARADO":
            raise IOError("Error while trying to stop the dome.")

        self.abortComplete(self.getAz())

    @lock
    def getAz(self):

        self._checkQuirk ()

        self.tty.setTimeout (10)

        cmd = "POSICAO?"

        self._write(cmd)

        ack = self._readline ()

        # check timeout
        if not ack:
            self.log.warning("Dome timeout, restarting it.")
            self._restartDome()
            return self.getAz()
            #raise IOError("Couldn't get azimuth after %d seconds." % 10)

        # uC is going crazy
        if ack == "INVALIDO":
            raise IOError("Error getting dome azimuth (ack=INVALIDO).")

        # get ack return
        if ack.startswith("CUPULA="):
            ack = ack[ack.find("=")+1:]

        if ack == "ERRO":
            self.log.warning("Dome position error, restarting it.")
            self._restartDome()
            return self.getAz()

        # correct dome/telescope phase difference
        az = int(math.ceil(int(ack)*self["az_resolution"]))
        az -= self._az_shift
        az = az % 360

        return Coord.fromDMS(az)

    @lock
    def openSlit (self):

        self._checkQuirk ()

        cmd = "ABRIR"

        self._write(cmd)

        ack = self._readline()

        if ack != "ABRINDO":
            raise IOError("Error trying to open the slit.")

        self.tty.setTimeout (self["open_timeout"])

        fin = self._readline ()

        # check timeout
        if not fin:
            raise IOError("Dome is still opening after "
                          "%d seconds" % self["open_timeout"])

        if not fin.startswith ("ABERTO"):
            raise IOError("Error opening slit.")

        self._slitOpen = True
        self.slitOpened(self.getAz())

    @lock
    def closeSlit (self):
        self._checkQuirk ()

        cmd = "FECHAR"

        self._write(cmd)

        ack = self._readline()

        if ack != "FECHANDO":
            raise IOError("Error trying to close the slit.")

        self.tty.setTimeout (self["close_timeout"])

        fin = self._readline ()

        # check timeout
        if not fin:
            raise IOError("Dome is still closing after "
                          "%d seconds" % self["close_timeout"])

        if not fin.startswith ("FECHADO"):
            raise IOError("Error closing slit.")

        self._slitOpen = False
        self.slitClosed(self.getAz())

    def isSlitOpen (self):
        return self._slitOpen

    @lock
    def lightsOn (self):

        self._checkQuirk ()

        cmd = "FLAT_ON"

        self._write(cmd)

        fin = self._readline()

        if fin != "FLAT_LIGADO":
            raise IOError("Error trying to turn lights on.")

    @lock
    def lightsOff (self):
        self._checkQuirk ()

        cmd = "FLAT_OFF"

        self._write(cmd)

        fin = self._readline()

        if fin != "FLAT_DESLIGADO":
            raise IOError("Error trying to turn lights off.")

    #
    # low level
    #

    def _debug(self, msg):
        if self._debugLog:
            print >> self._debugLog, time.time(), threading.currentThread().getName(), msg
            self._debugLog.flush()

    def _read(self, n = 1):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol="\n"):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        try:
            ret = self.tty.readline(None, eol)
        except select.error:
            ret = self.tty.readline(None, eol)

        self._debug("[read ] '%s'" % repr(ret).replace("'", ""))

        if ret:
            # remove eol marks
            return ret[:-3]
        else:
            return ""

    def _readbool(self, n = 1):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _busy_wait(self, n):
        t0 = time.time()
        i = 0
        while i < n:
            i+=1

    def _write(self, data, eol="\r"):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushOutput()

        self._busy_wait(1e6)

        self._debug("[write] '%s%s'" % (repr(data).replace("'", ""), repr(eol).replace("'","")))
        ret = self.tty.write("%s%s" % (data, eol))
        return ret
