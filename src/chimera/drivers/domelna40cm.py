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
import logging
import math
import sys

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.dome    import InvalidDomePositionException

from chimera.core.exceptions import ChimeraException
from chimera.core.lock import lock
from chimera.interfaces.domedriver import IDomeDriver

from chimera.util.coord import Coord


class DomeLNA40cm (ChimeraObject, IDomeDriver):

    def __init__(self):
        ChimeraObject.__init__ (self)

        self.tty = None
        self.abort = threading.Event ()

        self._slewing  = False
        self._slitOpen = False

        self._az_shift = 180

    def __start__ (self):
        self.open()
        return True

    def __stop__ (self):
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
            print "quirk", '"%"' % ret
            raise ChimeraException ("Quirk error!!!")

        return True

    @lock
    def open (self):

        self.tty = serial.Serial(self["device"], baudrate=9600,
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=self["init_timeout"], xonxoff=0, rtscts=0)


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
        dome_az = dome_az % 360
        
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
            # FIXME: restart the dome and try again
            raise IOError("Error while slewing dome. Some barcodes"
                          " couldn't be read correctly."
                          " Restarting the dome and trying again.")

        if fin.startswith ("CUPULA="):
            self._slewing = False
            time.sleep (0.3) # FIXME: how much sleep we need?
            self.slewComplete(self.getAz())
        else:
            self._slewing = False
            raise IOError("Unknow error while slewing. Received '%s' from dome." % fin)

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
            raise IOError("Couldn't get azimuth after %d seconds." % 10)

        # uC is going crazy
        if ack == "INVALIDO":
            raise IOError("Error getting dome azimuth (ack=INVALIDO).")

        # get ack return
        if ack.startswith("CUPULA="):
            ack = ack[ack.find("=")+1:]

        if ack == "ERRO":
            # FIXME: restart and try again
            raise ChimeraException ("Dome is in invalid state. Hard restart needed.")

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
            raise IOError("Dome is still opening after %d seconds" % self["open_timeout"])

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
            raise IOError("Dome is still closing after %d seconds" % self["close_timeout"])

        if not fin.startswith ("FECHADO"):
            raise IOError("Error closing slit.")

        self._slitOpen = False
        self.slitClosed(self.getAz())

    def isSlitOpen (self):
        return self._slitOpen


    #
    # low level
    #

    def _read(self, n = 1):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol="\n"):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        ret = self.tty.readline(None, eol)

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

    def _write(self, data, eol="\r"):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushOutput()

        return self.tty.write("%s%s" % (data, eol))
