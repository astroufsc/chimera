
import os
import ConfigParser

import numpy as np

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.cli import ChimeraCLI, action

from chimera.util.position import Position

from chimera.controllers.scheduler.model import (Session, Targets, Program, Point,
                                                 Expose, PointVerify, AutoFocus)

from chimera.core.site import (Site, datetimeFromJD)

import re

try:
	import _skysub
except ImportError:
	print '''To load chimera's TAO interface you need skycalc instaled. Skycalc can be downloaded at ().'''

cfgpath = os.path.dirname(__file__)

####################################################################################################################################

class MKQueue (ChimeraObject):
	'''
	A queue maker that operates with chimera for automated scheduling of observations. The input target lists are loaded
	as configuration files and individual targets for different projects can be separated with individual flags. These flags
	can then be used to apply different scheduling algorithms.
	
	Current algorithms are:
	
	1 - Standard stars:
	
		Observe a 'user defined' number of standard stars at a 'user defined' number of different airmasses throughout the night.

	2 - Lower airmass with specific conditions:
	
		Fill the night, or a 'user defined' portion of the night, with targets to be observed at the lower airmass as possible
		with a superior limit on airmass. 
		
		Available filters are:
			- Exposure time per filter
			- Moon: Filter selection based on moon brightness
			- Weather constraints: Seeing and Cloud cover.
		
		
	'''

	__config__ = {'sunMaxAlt'						: -18.}

	schedInfo = {	'targetFlag'					: '', # Main info
					'targetschedAlgorith'			: -1,
					'targetFilter'					: '',
					'targetExpTime'					: -1,
					'targetMaxAirmass'				: 1.8,
					'targetMaxMoonBright'			: 100.,
					'targetMinMoonBright'			: 0.,
					'targetMinMoonDist'				: 0.,
					'targetMaxSeeing'				: 1.8,
					'targetCloudCover'				: 0}
					
#					'sunMaxAlt'						: -18.}

	####################################################################################################################################
	
	def __init__(self):
		'''
		Constructor.
		'''
        
		ChimeraObject.__init__(self)
		
		self.sunMaxAlt = -18.
		self.isJD = False
		

	####################################################################################################################################
	
#	def __start__(self):
#
#		site=Site()
#		nowmjd=site.MJD()
#		self.setJD(nowmjd+2400000.5)
#		self.selectStandardTargets()
#		self.selectScienceTargets()

		
	####################################################################################################################################
	
	def setJD(self,jd=None):
		'''
		Configure time domain by specifing a julian day. It will use information on exposure time to build time bins that will be 
		filled when selecting targets.
		'''
		
		if not jd:
			site = Site()
			jd = np.floor(site.JD())+0.5

		print site['name']

		nightstart = site.JD(site.sunset_twilight_end()) #_skysub.jd_sun_alt(self.sunMaxAlt, jd, site.latitude, site.longitude)
		nightend   = site.JD(site.sunrise_twilight_begin()) #_skysub.jd_sun_alt(self.sunMaxAlt, jd+0.5, site.latitude, site.longitude)

		print('JD(%.3f) # Nigh Start @JD= %.3f # Night End @JD = %.3f'%(jd,nightstart,nightend))
		
		sitelat = np.sum(np.array([float(tt) / 60.**i for i,tt in enumerate(str(site['latitude']).split(':'))]))
		long = np.array([float(tt) / 60.**i for i,tt in enumerate(str(site['longitude']).split(':'))])
		long[1:] *= long[0]/np.abs(long[0])
		sitelong = np.sum(long)/180.*12.
		
		print site['latitude'],'->',sitelat
		print site['longitude'],'->',sitelong
		
		nightstart = _skysub.jd_sun_alt(self.sunMaxAlt, jd, sitelat, sitelong)
		nightend   = _skysub.jd_sun_alt(self.sunMaxAlt, jd+0.5, sitelat, sitelong)
		print('Nigh Start @JD= %.3f # Night End @JD = %.3f'%(nightstart,nightend))

		
		# Creating a 1 minute time bin
		tbin = 1./60./60./24.

		self.obsTimeBins = np.arange(nightstart,nightend+tbin,tbin)
		self.obsTimeMask = np.zeros(len(self.obsTimeBins))
		self.obsTimeMask[-1] = 1.0
		
		# Marking filled bins
		
		session = Session()
		
		scheduled = session.query(Program)
		
		for target in scheduled:
			tindex = np.abs(self.obsTimeBins - 2400000.5 - target.slewAt).argmin()
			self.obsTimeMask[tindex] = 1.0

		self.isJD = True

	####################################################################################################################################

	def selectScienceTargets(self):
		'''
		Based on configuration parameters select a good set of targets to run scheduler on a specified Julian Day.
		'''
		
		session = Session()
		
		# [To be done] Reject objects that are close to the moon

		for tbin,time in enumerate(self.obsTimeBins):

			if self.obsTimeMask[tbin] < 1.0:
				# Select objects from database that where not observed and where not scheduled yet
				# In the future may include targets that where observed a number of nights ago.
				# This is still incomplete. We should also consider the distance from the previous pointing to the next!
				# Since a target can have a higher airmass but be farther away from a neaby target that will take less time
				# to point.
				# one way of selecting targets that are close together and have good airmass is to select regions that are close
				# to the current location. it can start as searching an area with r1 ~ 10 x the FoV and, if there are no regions
				# to to x2 that and then x4 that. If still there are no targets, than search for the higher in the sky.
				targets = session.query(Targets).filter(Targets.observed == False).filter(Targets.scheduled == False).filter(Targets.type == self.sciFlag)
			
				lst = _skysub.lst(time,self.sitelong) #*360./24.
				alt = np.array([_skysub.altit(target.targetDec,lst - target.targetRa,self.sitelat)[0] for target in targets])
				stg = alt.argmax()

				self.log.info('Selecting %s'%(targets[stg]))
				
				# Marking target as schedule
				tst = session.query(Targets).filter(Targets.id == targets[stg].id)

				for t in tst:
					t.scheduled = True
					session.commit()
					self.addObservation(t,time)
				
				self.obsTimeMask[tbin] = 1.0
			else:
				self.log.debug('Bin %3i @mjd=%.3f already filled up with observations. Skipping...'%(tbin,time-2400000.5))
				
		#print i
		return 0 #targets

	####################################################################################################################################

	def selectStandardTargets(self,flag,nstars=3,nairmass=3):
		'''
		Based on configuration parameters, select 'nstars' standard stars to run scheduler on a specified Julian Day. Ideally you 
		will select standard stars before your science targets so not to have a full queue. Usually standard stars are observed 
		more than once a night at different airmasses. The user can control this parameter with nairmass and the script will try
		to take care of the rest. 
		'''

		session = Session()
		
		# First of all, standard stars can be observed multiple times in sucessive nights. I will mark all
		# stars an unscheduled.
		targets = session.query(Targets).filter(Targets.scheduled == True).filter(Targets.type == flag)
		for target in targets:
			target.scheduled = False
			session.commit()
		
		# [To be done] Reject objects that are close to the moon

		# Selecting standard stars is not only searching for the higher in that time but select stars than can be observed at 3
		# or more (nairmass) different airmasses. It is also important to select stars with different colors (but this will be
		# taken care in the future).

		if nairmass*nstars > len(self.obsTimeBins):
			self.log.warning('Requesting more stars/observations than it will be possible to schedule. Decreasing number of requests to fit in the night.')
			nstars = len(self.obsTimeBins)/nairmass

		obsStandars = np.zeros(len(self.obsTimeBins))-1 # first selection of observable standards

		site = Site()
		
		for tbin,time in enumerate(self.obsTimeBins):

			if self.obsTimeMask[tbin] < 1.0:
				# 1 - Select objects from database that where not scheduled yet (standard stars may be repited)
				#     that fits our observing night
				targets = session.query(Targets).filter(Targets.scheduled == 0).filter(Targets.type == flag)

				ephem = site._getEphem(datetimeFromJD(time))
				
				lst = np.sum(np.array([float(tt) / 60.**i for i,tt in enumerate(str(ephem.sidereal_time()).split(':'))]))
				sitelat = np.sum(np.array([float(tt) / 60.**i for i,tt in enumerate(str(site['latitude']).split(':'))]))
				alt = np.array([_skysub.altit(target.targetDec,lst - target.targetRa,sitelat)[0] for target in targets])
				stg = alt.argmax()

				self.log.info('Selecting %s'%(targets[stg]))
				
				# Marking target as schedule
				tst = session.query(Targets).filter(Targets.id == targets[stg].id)

				for t in tst:
					t.scheduled = True
					session.commit()
					obsStandars[tbin] = t.id
				
			else:
				self.log.info('Bin already filled up with observations. Skipping...')

		if len(obsStandars[obsStandars >= 0]) < nstars:
			self.log.warning('Could not find %i suitable standard stars in catalog. Only %i where found.'%(nstars,len(obsStandars[obsStandars >= 0])))
		#
		# Unmarking potential targets as scheduled
		#
		for id in obsStandars[obsStandars >= 0]:
			target = session.query(Targets).filter(Targets.id == id)
			for t in target:
				t.scheduled = False
				session.commit()
				
			tbin+=1
		#
		# Preparing a grid of altitudes for each target for each observing window
		#
		amGrid = np.zeros(len(obsStandars)*len(obsStandars)).reshape(len(obsStandars),len(obsStandars))

		for i in np.arange(len(obsStandars))[obsStandars >= 0]:
			target = session.query(Targets).filter(Targets.id == obsStandars[i])[0]
			for j in range(len(obsStandars)):
				lst = _skysub.lst(self.obsTimeBins[j],self.sitelong)
				amGrid[i][j] = _skysub.true_airmass(_skysub.secant_z(_skysub.altit(target.targetDec,lst - target.targetRa,self.sitelat)[0]))
				if amGrid[i][j] < 0:
					amGrid [i][j] = 99.
		#
		# Build a grid mask that specifies the position in time each target should be observed. This means that, when
		# selecting a single target we ocuppy more than one, non consecutive, position in the night. This grid shows where are these
		# positions.
		#
		obsMask = np.zeros(len(obsStandars)*len(obsStandars),dtype=np.bool).reshape(len(obsStandars),len(obsStandars))

		for i in np.arange(len(obsStandars))[obsStandars >= 0]:
			amObs = np.linspace(amGrid[i].min(),self.stdMaxAirmass,nairmass) # requested aimasses
			dam = np.mean(np.abs(amGrid[i][amGrid[i]<self.stdMaxAirmass][1:] - amGrid[i][amGrid[i]<self.stdMaxAirmass][:-1])) # how much airmass changes in average
			for j,am in enumerate(amObs):
				# Mark positions where target is at	specified airmass
				if j == 0:
					obsMask[i] = np.bitwise_or(obsMask[i],amGrid[i] == am)
				else:
					obsMask[i] = np.bitwise_or(obsMask[i],np.bitwise_and(amGrid[i]>am-dam,amGrid[i]<am+dam))

			#print amGrid[i][np.where(obsMask[i])]
		#
		# Now it is time to actually select the targets. It will start with the first target and then try the others
		# until it find enough standard stars, as specified by the user.
		#
		# Para cada bin em tempo, varro o bin em massa de ar por coisas observaveis. Se acho um, vejo se posso agendar
		# os outros bins. Se sim, marco o alvo para observacao, se nao, passo para o proximo. Repito ate completar a
		# lista de alvos
		#

		obsMaskTimeGrid = np.zeros(len(obsStandars),dtype=np.bool)
		nrequests = 0
		reqId = np.zeros(nstars,dtype=np.int)-1
		for tbin,time in enumerate(self.obsTimeBins[:-1]):
			# Evaluates if time slots are all available. If yes, mark orbservation and ocuppy slots.
			if ( (not obsMaskTimeGrid[obsMask[tbin]].any()) and (len(amGrid[tbin][obsMask[tbin]])>=nairmass) ):
				obsMaskTimeGrid = np.bitwise_or(obsMaskTimeGrid,obsMask[tbin])
				reqId[nrequests] = tbin
				nrequests += 1
			if nrequests >= nstars:
				break

		# Finally, requesting observations

		for id in reqId[reqId >= 0]:
			target = session.query(Targets).filter(Targets.id == obsStandars[id])[0]
			secz = amGrid[id][obsMask[id]]
			seczreq = np.zeros(nairmass,dtype=np.bool)
			amObs = np.linspace(amGrid[id].min(),self.stdMaxAirmass,nairmass) # requested aimasses
			for i,obstime in enumerate(self.obsTimeBins[obsMask[id]]):
				sindex = np.abs(amObs-secz[i]).argmin()
				if not seczreq[sindex]:
					self.log.info('Requesting observations of %s @airmass=%4.2f @mjd=%.3f...'%(target.name,secz[i],obstime-2400000.5))
					seczreq[sindex] = True
					target.scheduled = True
					session.commit()
					self.addObservation(target,obstime)
					self.obsTimeMask[obsMask[id]] = 1.0
			#print self.obsTimeBins[obsMask[id]]
			#print

		#print i
		return 0 #targets

	####################################################################################################################################

