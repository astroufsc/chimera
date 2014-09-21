#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2014 Alexandre Mello
# Driver for the JMI Smart Focuser 232 using serial communication

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
import serial
import time
import threading

from chimera.core.lock import lock

from chimera.interfaces.focuser import (FocuserFeature,
                                        InvalidFocusPositionException)

from chimera.instruments.focuser import FocuserBase

from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

__all__ = ['JMIsmart232']


class JMIsmart232 (FocuserBase):

    def __init__(self):
        FocuserBase.__init__(self)

        self.tty = None

        self._supports = {FocuserFeature.TEMPERATURE_COMPENSATION: False,
                          FocuserFeature.POSITION_FEEDBACK: True,
                          FocuserFeature.ENCODER: True}

        # debug log
        self._debugLog = None
        try:
            self._debugLog = open(
                os.path.join(SYSTEM_CONFIG_DIRECTORY, "jmismart-debug.log"), "w")
        except IOError, e:
            self.log.warning("Could not create meade debug file (%s)" % str(e))

    def __start__(self):
        self.open()
        self["model"] = "JMI Smart 232"
        return True

    def __stop__(self):
        self.close()
        return True

    @lock
    def open(self):

        self.tty = serial.Serial(self["device"],
                                 baudrate=9600,  # MUST be 9600 bits
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=None,
                                 xonxoff=False,
                                 rtscts=False)

        self.tty.timeout = self["open_timeout"]
        self.tty.open()
        self.tty.flushInput()
        self.tty.flushOutput()

        self["focuser_model"] = "JMI Smart 232"

        return True

    @lock
    def close(self):

        if self.tty.isOpen():
            self.tty.close()
            return True

    @lock
    def moveIn(self, n):
        target = self.getPosition() - n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % target)

    @lock
    def moveOut(self, n):
        target = self.getPosition() + n

        if self._inRange(target):
            self._setPosition(target)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % target)

    @lock
    def moveTo(self, position):
        if self._inRange(position):
            self._setPosition(position)
        else:
            raise InvalidFocusPositionException("%d is outside focuser "
                                                "boundaries." % int(position))

    @lock
    def getPosition(self):

        cmd = "p"

        self.tty.timeout = self["open_timeout"]

        self._write(cmd)

        ack = self._read(3)

        if not ack:
            # try again
            return self.getPosition()
            #raise IOError("Error getting focuser position (read timeout).")

        # parse ack and returns
        try:
            return int(ord(ack[1]) * 256 + ord(ack[2]))
        except ValueError, e:
            raise IOError(
                "Error getting focuser position. Invalid position returned")

    def getRange(self):
        return (0, 6600)

    def _setPosition(self, n):
        self.log.info("Changing focuser to %s" % n)

        cmd = "g" + ('%02x' % (int(n) / 256)).decode('hex') + \
            ('%02x' % (int(n) % 256)).decode('hex')

        self.tty.timeout = self["open_timeout"]

        self._write(cmd)

        ack = self._read(1)

        if not ack:
            raise IOError("Error moving the focuser (read timeout).")

        self.tty.timeout = 30  # Takes at least 30 seconds for a total sweep
        ack = self._read(1)  # Move confirmation
        if not ack:
            raise IOError("Error moving the focuser (read timeout).")

        if ack != 'c':
            raise ValueError("Error moving the focuser (not working).")

    def _inRange(self, n):
        min_pos, max_pos = self.getRange()
        return (min_pos <= n <= max_pos)

    def _debug(self, msg):
        if self._debugLog:
            print >> self._debugLog, time.time(
            ), threading.currentThread().getName(), msg
            self._debugLog.flush()

    def _read(self, n=1):

        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushInput()

        return self.tty.read(n)

    def _write(self, data):
        if not self.tty.isOpen():
            raise IOError("Device not open")

        self.tty.flushOutput()

        self._debug("[write] %s" % (repr(data)))

        return self.tty.write(data)
