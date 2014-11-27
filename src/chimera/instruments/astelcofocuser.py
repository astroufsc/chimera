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

import os
import serial
import time
import threading

from chimera.interfaces.focuser import (InvalidFocusPositionException,
										FocuserFeature)

from chimera.instruments.focuser import FocuserBase

from chimera.core.lock import lock
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.util.enum import Enum


from chimera.util.TSI.TSI import TSI
import chimera.util.TPL2.TPL2 as TPL2

Direction = Enum("IN", "OUT")


class AstelcoFocuser (FocuserBase):
	'''
AstelcoFocuser interfaces chimera with TSI system to control focus. System 
can be equiped with hexapod hardware. In this case, comunition is done in a 
vector. Temperature compensation can also be performed.
	'''

	__config__ = {'hexapod'		: True}

	def __init__ (self):
		FocuserBase.__init__ (self)

		self._supports = {	FocuserFeature.TEMPERATURE_COMPENSATION: True,
							FocuserFeature.POSITION_FEEDBACK: True,
							FocuserFeature.ENCODER: True}

		self._position = [0,0,0,0,0]
		self._range = None
		self._lastTimeLog = None

		self._tsi = None
		self._abort = threading.Event ()

		self._errorNo = 0
		self._errorString = ""

		# debug log
		self._debugLog = None
		try:
			self._debugLog = open(os.path.join(SYSTEM_CONFIG_DIRECTORY,
											   "astelcofocuser-debug.log"), "w")
		except IOError, e:
			self.log.warning("Could not create astelco debug file (%s)" % str(e))


		#self._user="admin"
		#self._password="admin"
		#self._aahost="localhost"
		#self._aaport="65432"
		print '--> INIT <--'


	def __start__(self):

		self.open()

		return True

	@lock
	def open(self):  # converted to Astelco
		print 'Connecting to Astelco server ',
		self._aahost,
		':',
		int(self._aaport)

		self._tpl = TPL2(user=self.user,
						password=self.password,
						host=self.host,
						port=int(self.port),
						echo=False,
						verbose=False,
						debug=True)
		print self._tpl.log

		try:
			self._tpl.open()

			self._checkAstelco()

			return True

		except (TPL2.SocketError, IOError):
			raise AstelcoException("Error while opening %s." % self["device"])

	@lock
	def close(self):  # converted to Astelco
		self.log.debug("TPl2 log:\n")
		for lstr in self._tpl.log:
			self.log.debug(lstr)
		if self._tpl.isListening():
			self._tpl.disconnect()
			return True
		else:
			return False

	def _move(self, direction, steps, axis=1):
		
		if not self._inRange(direction, steps):
			raise InvalidFocusPositionException(
												"%d is outside focuser limits." % steps)

		if direction not in Direction:
			raise ValueError("Invalid direction '%s'." % direction)

		self._moveTo(direction, steps)
		
		return True
