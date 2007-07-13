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

import logging
import sys

import serial

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.focuser import IFocuserDriver


class OptecTCFS (BasicLifeCycle, IFocuserDriver):

    def __init__ (self, manager):
        BasicLifeCycle.__init__ (self, manager)

        self.tty = None

        self._errorNo = 0
        self._errorString = ""


        self._directions = {"IN" : "FI",
                            "OUT": "FO"}

        self._modes = {"M": "Manual",
                       "F": "Free",
                       "A": "Auto-A",
                       "B": "Auto-B"}

    def init (self, config):
        self.config += config

        if not self.open ():
            return False

        return True

    def open(self):

        self.tty = serial.Serial(self.config.device,
                                 baudrate=19200,               #baudrate (MUST be 19200 bits)
                                 bytesize=serial.EIGHTBITS,    #number of databits
                                 parity=serial.PARITY_NONE,    #enable parity checking
                                 stopbits=serial.STOPBITS_ONE, #number of stopbits
                                 timeout=None,                 #set a timeout value, None for waiting forever
                                 xonxoff=0,                    #enable software flow control
                                 rtscts=0,                     #enable RTS/CTS flow control
                                 )

        try:

            self.tty.timeout = self.config.open_timeout
            self.tty.open()
            self.tty.flushInput ()
            self.tty.flushOutput ()
            
            if not self._setMode ("M"):
                logging.warning ("Couldn't put focuser on manual mode. Remote control will not work.")
                logging.warning (self.getError ()[1])
                return False

            if not self._ping():
                logging.warning ("OPTEC TCF-S is not responding at%s." %  self.config.device)
                return False

            return True

        except serial.SerialException, e:
            self.setError (-1, str(e))
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False
            
        except IOError,e:
            self.setError(e)
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False

    def close(self):
        if self.tty.isOpen():
            self.tty.close()
            return True
        else:
            self.setError(-1, "Device not open")
            return False

    def moveIn (self, n):
        return self._move ("IN", n)

    def moveOut (self, n):
        return self._move ("OUT", n)

    def moveTo (self, position):

        current = self.getPosition ()

        if current < 0:
            return False

        delta = position - current

        #   0 ------- 7000
        #  IN          OUT
        
        if delta > 0:
            return self._move ("OUT", abs(delta))
        elif delta < 0:
            return self._move ("IN", abs(delta))
        else:
            return True

    def _move (self, direction, steps):

        if steps < self.config.min_position or steps > self.config.max_position:
            self.setError (-1, "Trying to move outside focuser bounds.")
            return False

        if direction not in self._directions:
            self.setError (-1, "Invalid direction.")
            return False

        cmd = "%s%04d" % (self._directions[direction], steps)

        print "  move sent: %s" % cmd
        sys.stdout.flush ()

        self.tty.timeout = self.config.move_timeout
        
        self._write (cmd)

        ack = self._readline (eol="\r")

        print "  move ack: %s " % ack[:-2]
        sys.stdout.flush ()

        if not ack:
            self.setError (-1, "Error moving the focuser (read timeout).")
            return False

        if ack.startswith ("ER=2"):
            # boundary problem... when moving to an upper ow lower bound, ER=2 is returned and the usual * ack comes later
            ack = ack = self._readline (eol="\r")

            print "  move ack: %s " % ack[:-2]
            sys.stdout.flush ()
            
            if not ack:
                self.setError (-1, "Error moving the focuser (read timeout).")
                return False

        if not ack[:-2] == "*":        
            self.setError (-1, "Error moving the focuser (back ack).")
            return False

        return True


    def getPosition (self):

        cmd = "FPOSRO"
        
        self.tty.timeout = self.config.open_timeout

        print "  getPosition sent: %s" % cmd
        sys.stdout.flush ()
        
        self._write (cmd)

        ack = self._readline (eol="\r")

        print "  getPosition ack: %s" % ack
        sys.stdout.flush ()

        if not ack:
            self.setError (-1, "Error getting focuser position (read timeout).")
            return -1

        # parse ack and returns
        try:
            return int (ack[2:-2])
        except ValueError, e:
            self.setError (-1, "Error getting focuser position. Invalid position returned '%s'" % ack)
            return -1

    def _setMode (self, mode):

        if mode not in self._modes:
            self.setError (-1, "Invalid mode.")
            return False

        cmd = "F%sMODE" % mode

        # FIXME: well, bad protocol design: diferent modes have diferent ack messages,
        # we only support M mode right now.
        if mode != "M":
            self.setError (-1, "%s mode not supported." % self._modes[mode])
            return False

        self.tty.timeout = self.config.open_timeout

        print "  setMode sent: %s" % cmd
        sys.stdout.flush ()
       
        self._write (cmd)

        ack = self._readline (eol="\r")

        print "  setMode ack: %s" % ack
        sys.stdout.flush ()

        if not ack:
            self.setError (-1, "Error trying to set focuser mode to '%s' (read timeout)." % self._modes[mode])
            return False

        if not ack[:-2] == "!":        
            self.setError (-1, "Error setting focuser mode to '%s' (bad ack)." % self._modes[mode])
            return False

        return True

    def _ping (self):
        return True
    
    def _read(self, n = 1):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol="\r"):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

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
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushOutput()
        
        return self.tty.write("%s%s" % (data, eol))

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
