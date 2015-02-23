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
from chimera.core.exceptions import ChimeraException
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

from chimera.util.enum import Enum

from chimera.util.tpl2 import TPL2,SocketError

class AstelcoException(ChimeraException):
	pass

class AstelcoHexapodException(ChimeraException):
	pass

Direction = Enum("IN", "OUT")
Axis = Enum("X","Y","Z","U","V") # For hexapod

class AstelcoFocuser (FocuserBase):
	'''
AstelcoFocuser interfaces chimera with TSI system to control focus. System 
can be equiped with hexapod hardware. In this case, comunition is done in a 
vector. Temperature compensation can also be performed.
	'''

	__config__ = {	'user'	: 'admin',
					'password' : 'admin',
					'ahost' : 'localhost',
					'aport' : '65432',
					'hexapod' : True,
					'naxis'	: 5 ,
					'step' : 0.001,
					'unit' : 'mm'}

	def __init__ (self):
		FocuserBase.__init__ (self)

		self._supports = {	FocuserFeature.TEMPERATURE_COMPENSATION: False,
							FocuserFeature.POSITION_FEEDBACK: True,
							FocuserFeature.ENCODER: True}

		self._position = [0]*self['naxis']
		self._range = [None]*self['naxis']
		self._step = [None]*self['naxis']
		self._lastTimeLog = None

		self._tsi = None
		self._abort = threading.Event ()

		self._errorNo = 0
		self._errorString = ""

		self._poketime = 90.0
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
		#print '<--> INIT <-->'

	def __start__(self):

		print '-->FOCUS START<--'
		self.open()
		
		# range and step setting
		if self['hexapod']:
			for ax in Axis:
				min = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].OFFSET!MIN'%ax.index)
				max = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].OFFSET!MAX'%ax.index)
				step= self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].STEP'%ax.index)
				self._range[ax.index] = (min, max)
				self._step[ax.index] = self["step"]
				#if self._step[ax.index] == 'UNKNOWN':
				#	self._step[ax.index] = self["step"]
		else:
			min = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS.CURRPOS!MIN')
			max = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS.CURRPOS!MAX')
			self._range[Axis.Z.index] = (min,max)
			self._step[Axis.Z.index] = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS.STEP')

		return True
	
	def __stop__(self):
		self.close()

	def __main__(self):
		pass

	def naxis(self):
		return len(self._position)

	def helloTPL(self):
		self.log.debug(self._tpl.getobject('SERVER.UPTIME'))
		self.sayhello = threading.Timer(self._poketime,self.helloTPL)
		self.sayhello.start()

	@lock
	def open(self):  # converted to Astelco
		self.log.info('Connecting to Astelco server %s:%i'%(self["ahost"],
															int(self["aport"])))

		self._tpl = TPL2(user=self['user'],
						password=self['password'],
						host=self['ahost'],
						port=int(self['aport']),
						echo=False,
						verbose=False,
						debug=True)
		self.log.debug(self._tpl.log)

		try:
			self._tpl
			self._tpl.get('SERVER.INFO.DEVICE')
			self._tpl.received_objects
			print self._tpl.getobject('SERVER.UPTIME')
			self._tpl
				
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

	@lock
	def moveIn(self, n, axis='Z'):
		ax = self.getAxis(axis)
		target = self.getOffset()[ax.index] - n*self._step[ax.index]

		self.log.debug('Setting offset on %s-axis to %f %s ...'%(ax,target,self['unit']))
		
		if self._inRange(target,ax):
			self._setPosition(target,ax)
		else:
			raise InvalidFocusPositionException("%d is outside focuser "
												"boundaries." % target)

	@lock
	def moveOut(self, n, axis='Z'):
		ax = self.getAxis(axis)
		
		target = self.getOffset()[ax.index] + n*self._step[ax.index]
		
		self.log.debug('Setting offset on %s-axis to %f %s ...'%(ax,target,self['unit']))

		if self._inRange(target,ax):
			self._setPosition(target,ax)
		else:
			raise InvalidFocusPositionException("%d is outside focuser "
												"boundaries." % target)

	@lock
	def moveTo(self, position,axis='Z'):
		ax = self.getAxis(axis)
		
		self.log.debug('Setting offset on %s-axis to %f %s ...'%(ax,position*self._step[ax.index],self['unit']))
		
		#return 0
		
		if self._inRange(position*self._step[ax.index],ax):
			self._setPosition(position*self._step[ax.index],ax)
		else:
			raise InvalidFocusPositionException("%f %s is outside focuser "
												"boundaries." % (position*self._step[ax.index],
												self["unit"]))

	@lock
	def getOffset(self):

		if self['hexapod']:
			pos = [0]*self['naxis']
			for iax in range(self['naxis']):
				pos[iax] = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].OFFSET'%iax)
			return pos
		else:
			return self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS.OFFSET')


	@lock
	def getPosition(self):

		return self.getOffset()
		
		if self['hexapod']:
			pos = [0]*self['naxis']
			for iax in range(self['naxis']):
				pos[iax] = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].REALPOS'%iax)
			return pos
		else:
			return self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS.REALPOS')


	def getRange(self,axis='Z'):
		return self._range[self.getAxis(axis).index]

	def _setPosition(self, n, axis=Axis.Z):
		self.log.info("Changing focuser offset to %s" % n)
		
		cmdid = None
		
		if self['hexapod']:
			cmdid = self._tpl.set('POSITION.INSTRUMENTAL.FOCUS[%i].OFFSET'%axis.index,n)
		else:
			cmdid = self._tpl.set('POSITION.INSTRUMENTAL.FOCUS.OFFSET',n)
		
		if not cmdid:
			msg = "Could not change focus offset to %f %s"%(position*self._step[ax.index],
															self["unit"])
			self.log.error(msg)
			raise InvalidFocusPositionException(msg)
		
		cmdComplete = False
		while not cmdComplete:
		
			for line in self._tpl.commands_sent[cmdid]['received']:
				self.log.debug(line[:-1])
				if line.find('COMPLETE') > 0:
					cmdComplete = True
			time.sleep(1.0)

		# check limit state
		LSTATE = self._tpl.getobject('POSITION.INSTRUMENTAL.FOCUS[%i].LIMIT_STATE'%axis.index)
		code = '%16s'%(bin(LSTATE)[2:][::-1])
		bitcode = [0,1,7,8,9,15]
		LMESSG = ['MINIMUM HARDWARE LIMIT',
				  'MAXIMUM HARDWARE LIMIT',
				  'HARDWARE BLOCK',
				  'MINIMUM SOFTWARE LIMIT',
				  'MAXIMUM SOFTWARE LIMIT',
				  'SOFTWARE BLOCK']
		STATE = True
		msg = ''
		for ib,bit in enumerate(bitcode):
			if code[bit] == '1':
				STATE = False
				msg += LMESSG[ib] + '|'
		
		
		if not STATE:
			msg='LIMIT STATE [%i] REACHED on %s-axis: %s'%(LSTATE,
														   axis,
														   msg)
			self.log.error(msg)
			raise InvalidFocusPositionException(msg)
			return -1

		self._position[axis.index] = n

		return 0

	def _inRange(self, n,axis=Axis.Z):
		min_pos, max_pos = self.getRange(axis)
		if not min_pos or not max_pos:
			self.log.warning('Minimum and maximum positions not defined...')
			return True
		return (min_pos <= n <= max_pos)

	def getAxis(self,axis=Axis.Z):

		if type(axis) == str:
			return Axis.fromStr(axis)
		elif type(axis) == int:
			return Axis[axis]
		elif type(axis) == type(Axis.Z):
			return axis
		else:
			ldir = ''
			for i in Axis:
				ldir+=str(i)
			raise AstelcoHexapodException('Direction not valid! Try one of %s'%ldir)


'''





	def _move(self, direction, steps,axis=Axis.Z):

		if direction not in Direction:
			raise ValueError("Invalid direction '%s'." % direction)

		if axis not in Axis:
			raise ValueError("Invalid axis '%s'." % axis)

		if not self._inRange(direction, steps, axis):
			raise InvalidFocusPositionException(
												"%d is outside focuser limits." % steps)
		
		self._moveTo(direction, steps, Axis.Z)
		
		return True


	def _inRange(self, direction, n, axis=Axis.Z):

		# Assumes:
		#   0 -------  N
		#  IN         OUT

		current = self.getPosition(axis)

		if direction == Direction.IN:
			target = current - n
		else:
			target = current + n

		min_pos, max_pos = self.getRange(axis)

		return (min_pos <= target <= max_pos)


	def getPosition(self,axis=Axis.Z):
		return self._position[axis]

	def getRange(self,axis=Axis.Z):
		return self._range[axis]

'''