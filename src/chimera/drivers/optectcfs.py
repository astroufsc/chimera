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

import logging
import sys

import serial

from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.focuser       import InvalidFocusPositionException
from chimera.interfaces.focuserdriver import IFocuserDriver

from chimera.core.lock import lock

from chimera.util.enum import Enum


__all__ = ['OptecTCFS']


Mode      = Enum("Manual", "Free", "Auto_A", "Auto_B")
Direction = Enum("IN", "OUT")


class OptecTCFS (ChimeraObject, IFocuserDriver):

    def __init__ (self):
        ChimeraObject.__init__ (self)

        self.tty = None

        self._directions = {Direction.IN : "FI",
                            Direction.OUT: "FO"}

        self._modes = {Mode.Manual: "M",
                       Mode.Free  : "F",
                       Mode.Auto_A: "A",
                       Mode.Auto_B: "B"}

    def __start__ (self):
        self.open()
        return True

    def __stop__ (self):
        self.close()
        return True

    @lock
    def open(self):

        self.tty = serial.Serial(self["device"],
                                 baudrate=19200, # MUST be 19200 bits
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=None,
                                 xonxoff=False,
                                 rtscts=False)

        self.tty.timeout = self["open_timeout"]
        self.tty.open()
        self.tty.flushInput ()
        self.tty.flushOutput ()
        
        self._setMode (Mode.Manual)

        return True

    @lock
    def close(self):

        if self.tty.isOpen():
            self.tty.close()
            return True

    @lock
    def moveIn (self, n):
        return self._move (Direction.IN, n)

    @lock
    def moveOut (self, n):
        return self._move (Direction.OUT, n)

    @lock
    def moveTo (self, position):

        current = self.getPosition ()

        if current < 0:
            return False

        delta = position - current

        #   0 ------- 7000
        #  IN          OUT
        
        if delta > 0:
            return self._move (Direction.OUT, abs(delta))
        elif delta < 0:
            return self._move (Direction.IN, abs(delta))
        else:
            return True

    def _move (self, direction, steps):

        if steps < self["min_position"] or steps > self["max_position"]:
            raise InvalidFocusPositionException("%d is outside focuser limits." % steps)
        
        if direction not in Direction:
            raise ValueError("Invalid direction '%s'." % direction)

        cmd = "%s%04d" % (self._directions[direction], steps)

        self.log.debug ("  move sent: %s" % cmd)
        sys.stdout.flush ()

        self.tty.timeout = self["move_timeout"]
        
        self._write (cmd)

        ack = self._readline (eol="\r")

        self.log.debug ("  move ack: %s " % ack[:-2])
        sys.stdout.flush ()

        if not ack:
            raise IOError("Error moving the focuser (read timeout).")

        if ack.startswith ("ER=2"):
            # boundary problem... when moving to an upper ow lower bound,
            #ER=2 is returned and the usual * ack comes later
            ack = ack = self._readline (eol="\r")

            self.log.debug ("  move ack: %s " % ack[:-2])
            sys.stdout.flush ()
            
            if not ack:
                raise IOError("Error moving the focuser (read timeout).")

        if not ack[:-2] == "*":        
            raise ValueError("Error moving the focuser (bad ack).")

        return True

    @lock
    def getPosition (self):

        cmd = "FPOSRO"
        
        self.tty.timeout = self["open_timeout"]

        self.log.debug ("  getPosition sent: %s" % cmd)
        sys.stdout.flush ()
        
        self._write (cmd)

        ack = self._readline (eol="\r")

        self.log.debug ("  getPosition ack: %s" % ack)
        sys.stdout.flush ()

        if not ack:
            raise IOError("Error getting focuser position (read timeout).")

        # parse ack and returns
        try:
            return int (ack[2:-2])
        except ValueError, e:
            raise IOError("Error getting focuser position. Invalid position returned '%s'" % ack)

    def _setMode (self, mode):

        if mode not in Mode:
            raise ValueError("Invalid mode '%s'." % mode)

        cmd = "F%sMODE" % mode

        # FIXME: well, bad protocol design: diferent modes have diferent ack messages,
        # we only support M mode right now.
        if mode != Mode.Manual:
            raise NotImplementedError("%s mode not supported." % mode)

        self.tty.timeout = self["open_timeout"]

        self.log.debug ("  setMode sent: %s" % cmd)
        sys.stdout.flush ()
       
        self._write (cmd)

        ack = self._readline (eol="\r")

        self.log.debug ("  setMode ack: %s" % ack)
        sys.stdout.flush ()

        if not ack:
            raise IOError("Error trying to set focuser mode"
                          " to '%s' (read timeout)." % self._modes[mode])

        if not ack[:-2] == "!":        
            raise IOError("Error setting focuser mode to '%s' (bad ack)." % mode)

        return True

    def _ping (self):
        return True
    
    def _read(self, n = 1):

        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol="\r"):

        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()
        
        ret = self.tty.readline(None, eol)

        if ret:
            return ret
        else:
            return ""

    def _readbool(self, n = 1):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _write(self, data, eol=""):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushOutput()
        
        return self.tty.write("%s%s" % (data, eol))

