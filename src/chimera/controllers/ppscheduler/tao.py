
import os
import ConfigParser

import numpy as np

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.cli import ChimeraCLI, action

from chimera.controllers.scheduler.model import (Session, Targets)

try:
	import _skysub
except ImportError:
	print '''To load chimera's TAO interface you need skycalc instaled. Skycalc can be downloaded at ().'''

cfgpath = os.path.dirname(__file__)

####################################################################################################################################

class TAO (ChimeraObject):
	'''
	An interface with TAO for a seamless preparation of observations queue from target files. The input target lists are loaded 
	as configuration files and should be separated in one file for standard stars and another for science targets. 
	'''

	__config__ = {	'stdFlag'    : 'c',
			'sciFlag'    : 's',
			'stdUser'    : 'CAL',
			'sciUser'    : 'SMP',
			'stdExpTime' : [60,60,60,60,60,10],
			'sciExpTime' : [60,60,60,60,60,10],
			'PATH'	     : '~/TAO/targets',
			'sitelat'    : -30.228,
			'sitelong'   : 4.715,
			'sunMaxAlt'  : -18,
			'filters'    : [U, B, V, R, I, clear],
			'nfilters'   : 6}

	####################################################################################################################################
	
	def __init__(self):
		'''
		Constructor.
		'''
        
		ChimeraObject.__init__(self)
		
		#
		# Reading in configuration parameters
		#
		config = ConfigParser.RawConfigParser()
		
		if os.path.exists(os.path.join(os.path.expanduser('~/.TAO'),'tao.cfg')):
			config.read(os.path.join(os.path.expanduser('~/.TAO'),'tao.cfg'))
		else:
			self.log.warning('No user defined configuration found at %s. Using default values.'%(os.path.join(os.path.expanduser('~/.TAO'),'tao.cfg')))
			config.read(os.path.join(os.path.join(cfgpath,'../../tao.cfg')))

		#
		# Setting configuration parameters
		#
		self.stdFlag = config.get('TargetsInfo', 'Standard')
		self.sciFlag = config.get('TargetsInfo', 'Science')
		self.stdUser = config.get('TargetsInfo', 'stdUser')
		self.sciUser = config.get('TargetsInfo', 'sciUser')
		self.stdFile = config.get('TargetsInfo', 'stdFile')
		self.sciFile = config.get('TargetsInfo', 'sciFile')
		self.PATH = os.path.expanduser(config.get('Local', 'PATH'))
		
		self.sitelat = float(config.get('Site','sitelat'))
		self.sitelong = float(config.get('Site','sitelong'))
		self.sunMaxAlt = float(config.get('Site','sunMaxAlt'))
		
		self.filters = [i.replace(' ', '') for i in config.get('Instrument', 'Filters').split(',')]
		self.nfilters = len(self.filters)
		self.stdExpTime = [float(i) for i in config.get('TargetsInfo', 'stdExpTime').split(',')]
		self.sciExpTime = [float(i) for i in config.get('TargetsInfo', 'sciExpTime').split(',')]


		#
		# These are time bins, which breaks the night in timely intervals. Bins is the time at the begining of the bin
		# and Mask is percent full. 
		self.obsTimeBins = []
		self.obsTimeMask = []
		
	####################################################################################################################################

	def setJD(self,jd):
		'''
		Configure time domain by specifing a julian day. It will use information on exposure time to build time bins that will be 
		filled when selecting targets.
		'''
		
		nightstart = _skysub.jd_sun_alt(self.sunMaxAlt, jd, self.sitelat, self.sitelong)
		nightend   = _skysub.jd_sun_alt(self.sunMaxAlt, jd+0.5, self.sitelat, self.sitelong)
		
		tbin = np.max([np.max(self.sciExpTime),np.max(self.stdExpTime)])*self.nfilters

		self.obsTimeBins = np.arange(nightstart,nightend+tbin,tbin)
		self.obsTimeMask = np.zeros(len(self.obsTimeMask))

	####################################################################################################################################

	def selectScienceTargets(self):
		'''
		Based on configuration parameters select a good set of targets to run scheduler on a specified Julian Day.
		'''
		
		session = Session()
		
		# [To be done] Reject objects that are close to the moon
		
		self.log.debug('Selecting targets.')

		for time in self.obsTimeBins[:-1]:

			# Select objects from database that where not observed and where not scheduled yet
			# In the future may include targets that where observed a number of nights ago.
			targets = session.query(Targets).filter(Targets.observed == 0).filter(Targets.type == self.sciFlag)
			
			lst = _skysub.lst(time,self.sitelong) #*360./24.
			alt = np.array([_skysub.altit(target.targetDec,lst - target.targetRa,self.sitelat)[0] for target in targets])
			stg = alt.argmax()

			self.log.info('Selecting %s'%(targets[stg]))
			targets[stg].observed = -1 # Marking target as scheduled

			session.commit()
			#targets[tbin] = xaxis[stg]

			#tbin+=1
		#print i
		return 0 #targets


	####################################################################################################################################
