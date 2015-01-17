
import os
import ConfigParser

import numpy as np

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.cli import ChimeraCLI, action

from chimera.util.position import Position

from sqlalchemy import desc

from chimera.controllers.scheduler.model import (Session, Targets, Program, Point,
                                                 Expose, PointVerify, AutoFocus,
												 ObsBlock, BlockConfig, BlockPar)

from chimera.core.site import (Site, datetimeFromJD)

import re

################################################################################
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

	####################################################################################################################################
	
	def __init__(self):
		'''
		Constructor.
		'''
        
		ChimeraObject.__init__(self)

		self.slotLen = 60. # duration of observation slot in seconds
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

	def selectScienceTargets(self,FLAG):
		'''
        Based on configuration parameters select a good set of targets to run scheduler on a specified Julian Day.
        '''

		session = Session()
		
		targets = session.query(ObsBlock).filter(ObsBlock.pid == FLAG).filter(ObsBlock.scheduled == True) #,Targets,BlockConfig,BlockPar).filter(ObsBlock.pid == FLAG).join(Targets).join(BlockConfig).join((BlockPar,BlockPar.bid == BlockConfig.bparid))
		
		for target in targets:
			target.scheduled = False
			session.commit()

		site = Site()

        # [To be done] Reject objects that are close to the moon

		nightstart = site.sunset_twilight_end()
		nightend   = site.sunrise_twilight_begin()

		# Creat observation slots.

		obsSlots = np.array(np.arange(site.MJD(nightstart),site.MJD(nightend),self.slotLen/60./60./24.),
						    dtype= [ ('start',np.float),
									 ('end',np.float)  ,
									 ('slotid',np.int)] )

		obsSlots['end'] += self.slotLen/60./60/24.
		obsSlots['slotid'] = np.arange(len(obsSlots))

		obsTargets = np.array([],dtype=[('obsblock',ObsBlock),('targets',Targets),('blockid',np.int)])


		# For each slot select the higher in the sky...
		# [TBD] - avoid moon
		targets = session.query(ObsBlock,Targets).filter(ObsBlock.pid == FLAG,ObsBlock.scheduled==False,ObsBlock.observed==False).join(Targets)

		for itr in range(len(obsSlots)):

				ephem = site._getEphem(datetimeFromJD(obsSlots['start'][itr]+2400000.5))

				lst = ephem.sidereal_time() # in radians
				#sitelat = np.sum(np.array([float(tt) / 60.**i for i,tt in enumerate(str(site['latitude']).split(':'))]))
				alt = np.array([float(site.raDecToAltAz(Position.fromRaDec(target[1].targetRa,target[1].targetDec),lst).alt) for target in targets])

				stg = alt.argmax()
				s_target = targets[stg]

				if not targets[stg][0].blockid in obsTargets['blockid']:
					self.log.debug('#%s %i %i %f: lst = %f | ra = %f | scheduled = %i'%(s_target[0].pid,stg,targets[stg][0].blockid,obsSlots['start'][itr],lst,s_target[1].targetRa,targets[stg][0].scheduled))
										
					obsTargets = np.append( obsTargets, np.array((s_target[0],s_target[1],targets[stg][0].blockid),dtype=[('obsblock',ObsBlock),('targets',Targets),('blockid',np.int)]))
					
					self.addObservation(s_target[0],obsSlots['start'][itr])
					targets[stg][0].scheduled = True
					session.commit()
				
				else:
					self.log.debug('#Block already scheduled#%s %i %i %f: lst = %f | ra = %f | scheduled = %i'%(s_target[0].pid,stg,targets[stg][0].blockid,obsSlots['start'][itr],lst,s_target[1].targetRa,targets[stg][0].scheduled))
							
		print len(obsTargets)
		return 0

        '''
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
'''
	#
	############################################################################
	#
	
	def selectStandardTargets(self,FLAG,nstars=3,nairmass=3):
		'''
Based on configuration parameters, select 'nstars' standard stars to run the
scheduler on a specified Julian Day. Ideally you will select standard stars 
before your science targets so not to have a full queue. Usually standard stars 
are observed more than once a night at different airmasses. The user can control
this parameter with nairmass and the script will try to take care of the rest.
		'''

		session = Session()
		
		# First of all, standard stars can be observed multiple times in
		# sucessive nights. I will mark all stars an unscheduled.
		targets = session.query(ObsBlock).filter(ObsBlock.pid == FLAG) #,Targets,BlockConfig,BlockPar).filter(ObsBlock.pid == FLAG).join(Targets).join(BlockConfig).join((BlockPar,BlockPar.bid == BlockConfig.bparid))
		
		for target in targets:
			target.scheduled = False
			session.commit()

		# [TBD] Reject objects that are close to the moon

		# Selecting standard stars is not only searching for the higher in that
		# time but select stars than can be observed at 3 or more (nairmass)
		# different airmasses. It is also important to select stars with
		# different colors (but this will be taken care in the future).

		# [TBD] Select by color also
		
		#if nairmass*nstars > len(self.obsTimeBins):
		#	self.log.warning('Requesting more stars/observations than it will be possible to schedule. Decreasing number of requests to fit in the night.')
		#	nstars = len(self.obsTimeBins)/nairmass

		# Build queue with objects already alocated
		
		programs = session.query(Program).filter(Program.finished == False).all()
		obsQueue = np.array(np.zeros(len(programs[:])),
							dtype=[ ('start',np.float),('end',np.float)])

		site = Site()
		for i,program in enumerate(programs):
			if site.sunset_twilight_end() < program.slewAt < site.sunrise_twilight_begin():
				expose = session.query(Expose).filter(expose.id == program.id)
				obsQueue['start'][i] = program.slewAt if program.slewAt > 0. else program.exposeAt
				obsQueue['end'][i] = program.exposeAt
				for exp in expose:
					obsQueue['end'][i] += exp.frames * exp.exptime

		if len(obsQueue) > 0:
			# sort result with increasing start time
			asort = obsQueue['start'].argsort()
			obsQueue['start'] = obsQueue['start'][asort]
			obsQueue['end'] = obsQueue['end'][asort]
		else:
			obsQueue = np.array(np.zeros(1)+site.MJD(site.sunrise_twilight_begin()),
								dtype=[ ('start',np.float),('end',np.float)])

		# check that queue makes sense
		if checkQueue(obsQueue):
			msg = '''Looks like there is a problem with the queue definition. Usually this means
that there are overlaping observations. Try cleaning the queue and start over.'''
			self.log.error(msg)
			raise IOError(msg)
		
		# Create empty slot arrays where there can be objects scheduled
		emptySlots = np.array([],
							  dtype=[ ('start',np.float),
									  ('end',np.float)  ,
									  ('slotid',np.int)] )

		time = site.MJD(site.sunset_twilight_end()) # time at start of the night
		block = 0

		while ( time < site.MJD(site.sunrise_twilight_begin()) and block < len(obsQueue) ):

			if time < obsQueue['start'][block]:
				obsSlots = np.arange(time,
									obsQueue['start'][block],
									 self.slotLen/60./60/24.)
				newslots = np.array(np.zeros(len(obsSlots)-1)+block,
									 dtype=[ ('start',np.float),
											 ('end',np.float),
											 ('slotid',np.int)])
				newslots['start'] = obsSlots[:-1]
				newslots['end'] = obsSlots[1:]
				emptySlots = np.append(emptySlots,newslots)
									   
			time = obsQueue['end'][block]
			block += 1

		if len(emptySlots) == 0:
			self.log.warning('No slots available. Try reseting the queue.')
			return -1
		else:
			self.log.debug('%i slots available'%(len(obsSlots)))

		time = site.MJD(site.sunset_twilight_end()) # time at start of the night
		sched = True # Flag to stop scheduler
		block = 0 # iterator over observing blocks
		obsStandars = np.array([],dtype=[('obsblock',ObsBlock),('targets',Targets)])
		obsStandarsStart = np.array([])
		obsStandarsEnd = np.array([])
		
		# Pre-select all available standard stars that fits observing windows
		#.join(BlockConfig).join((BlockPar,BlockPar.bid == BlockConfig.bparid))

		while sched:

			if time < obsQueue['start'][block]:
				# 1 - Select objects from database that where not scheduled yet
				# that fits our observing night (standard stars may be repited)
				#targets = session.query(Targets).filter(Targets.scheduled == 0).filter(Targets.type == flag)
				#targets = session.query(ObsBlock).filter(ObsBlock.scheduled == True).filter(ObsBlock.pid == FLAG).join(Targets).join(BlockConfig).join((BlockPar,BlockPar.bid == BlockConfig.bparid))

				targets = session.query(ObsBlock,Targets).filter(ObsBlock.pid == FLAG,ObsBlock.scheduled==False).join(Targets)
				ephem = site._getEphem(datetimeFromJD(time+2400000.5))

				lst = ephem.sidereal_time() # in radians
				#sitelat = np.sum(np.array([float(tt) / 60.**i for i,tt in enumerate(str(site['latitude']).split(':'))]))
				alt = np.array([float(site.raDecToAltAz(Position.fromRaDec(target[1].targetRa,target[1].targetDec),lst).alt) for target in targets])

				stg = alt.argmax()
				
				s_target = targets[stg]
				
				self.log.debug('#%s %i %i %f %f: lst = %f | ra = %f'%(s_target[0].pid,stg,targets[stg][0].blockid,time,obsQueue['start'][block],lst,s_target[1].targetRa))
				#blockid = targets[stg][0].blockid
				tmp = session.query(BlockConfig).filter(ObsBlock.pid == FLAG, BlockConfig.bid == s_target[0].blockid)
				# Check if observation fits in current window
				dT = 0.
				for t in tmp:
					dT += t.nexp * t.exptime/60./60./24.
				
				self.log.debug('dT = %f'%dT)
				
				if time+dT < obsQueue['start'][block]: # Ok, fits!
					self.log.debug('Block fits...')
					#targets[stg][0].scheduled = True
					#session.commit()
					
					for t in tmp:
						obsStandars = np.append( obsStandars, np.array(s_target,dtype=[('obsblock',ObsBlock),('targets',Targets)]))
						obsStandarsStart = np.append( obsStandarsStart, time)
						obsStandarsEnd = np.append( obsStandarsEnd, time+dT)
					
					time+=dT
				elif time >= site.MJD(site.sunrise_twilight_begin()):
					sched = False
				else: # does not fit :(
					self.log.debug('Block does not fit. Skipping...')
					time = obsQueue['end'][block]
					block += 1
					if block >= len(obsQueue):
						self.log.debug('Night is over...')
						sched = False

			else:
				self.log.debug('Bin already filled up with observations. Skipping...')
				time = ObsBlock['end'][block]
				block += 1
				if block >= len(obsQueue):
					sched = False

		if len(obsStandars) < nstars:
			self.log.warning('Could not find %i suitable standard stars in catalog. Only %i where found.'%(nstars,len(obsStandars[obsStandars >= 0])))
		elif len(obsStandars) == 0:
			self.log.warning('Could not find suitable targets. Job done.')
			return -1

		# Don;t need this anymore since I already have a list of targets
		#
		# Unmarking potential targets as scheduled
		#
		#for id in obsStandars:
		#	target = session.query(ObsBlock).filter(ObsBlock.id == obsStandars[i])
		#	for t in target:
		#		t.scheduled = False
		#		session.commit()
		#
		#	tbin+=1

		#
		# Preparing a grid of altitudes for each target for each observing window
		#
		amGrid = np.zeros(len(obsStandars)*len(emptySlots)).reshape(len(obsStandars),len(emptySlots))
		self.log.info('Preparing grid of altitudes for each target for each observing window...')
		
		for i in np.arange(len(obsStandars)):

			target = obsStandars['targets'][i] #session.query(ObsBlock).join(Targets).filter(ObsBlock.id == obsStandars[i])[0]
			for j in range(len(emptySlots)):
				time = (emptySlots['start'][j]+emptySlots['end'][j])/2.
				ephem = site._getEphem(datetimeFromJD(time+2400000.5))
				altAz = site.raDecToAltAz(Position.fromRaDec(target.targetRa,target.targetDec),float(ephem.sidereal_time()))
				#amGrid[i][j] = float(altAz.alt)
				
				amGrid[i][j] = site.sec_z(float(altAz.alt))
				if float(altAz.alt) < 10:
					amGrid [i][j] = site.sec_z(10.)
				#elif amGrid[i][j] > 5.0:
				#	amGrid[i][j] = 5.0
				

		#
		# Build a grid mask that specifies the position in time each target should be observed. This means that, when
		# selecting a single target we ocuppy more than one, non consecutive, position in the night. This grid shows where
		# these positions are.
		#
		self.log.info('Build a grid mask specifing the position in time each target should be observed...')
		
		obsMask = np.zeros(len(obsStandars)*len(emptySlots),dtype=np.bool).reshape(len(obsStandars),len(emptySlots))
		blockDuration = np.zeros(len(obsStandars)) # store duration of each block
		maxAirmass = np.zeros(len(obsStandars)) # store max airmass of each block
		
		for i in np.arange(len(obsStandars)):

			blockInfo = session.query(BlockConfig).filter(BlockConfig.pid == FLAG,BlockConfig.bid == obsStandars['obsblock'][i].blockid)
			blockPar = session.query(BlockPar).filter(BlockPar.pid == FLAG, BlockPar.bid == blockInfo[0].bparid).first()
			
			
			for b in blockInfo:
				self.log.debug(b)
				blockDuration[i] += b.nexp * b.exptime/60./60./24.
			if blockPar.maxairmass > 1.0:
				maxAirmass[i] = blockPar.maxairmass
			else:
				maxAirmass[i] = 3.0
			
			amObs = np.linspace(amGrid[i].min(),maxAirmass[i],nairmass) # requested aimasses
			dam = np.mean(np.abs(amGrid[i][1:] - amGrid[i][:-1])) # how much airmass changes in average
			for j,am in enumerate(amObs):
				self.log.debug('GridPos: %4i | Airmass: %5.2f'%(j,am))
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

		self.log.info('Selecting apropriate targets...')
		
		obsMaskTimeGrid = np.zeros(len(emptySlots),dtype=np.bool)
		nrequests = 0
		reqId = np.zeros(nstars,dtype=np.int)-1
		
		for tbin in range(obsMask.shape[0]):
			# Evaluates if time slots are all available. If yes, mark orbservation and ocuppy slots.
			if ( ( not obsMaskTimeGrid[obsMask[tbin]].any() ) \
				  and (len(amGrid[tbin][obsMask[tbin]])>=nairmass) ):
				obsMaskTimeGrid = np.bitwise_or(obsMaskTimeGrid,obsMask[tbin])
				reqId[nrequests] = tbin
				nrequests += 1
			if nrequests >= nstars:
				break

		if nrequests >= nstars:
			self.log.info('Found %i suitable standard stars... Scheduling...'%(nrequests))
		else:
			self.log.warning('Could not find enough standard stars to fill the requested number. Found %i of %i...'%(nrequests, nstars))

		# Finally, requesting observations

		for id in reqId[reqId >= 0]:
			secz = amGrid[id][obsMask[id]]
			seczreq = np.zeros(nairmass,dtype=np.bool)
			amObs = np.linspace(amGrid[id].min(),maxAirmass[id],nairmass) # requested aimasses
			for i,obstime in enumerate(emptySlots['start'][obsMask[id]]):
				sindex = np.abs(amObs-secz[i]).argmin()
				if not seczreq[sindex]:
					self.log.debug('Requesting observations of %s [@airmass=%4.2f | mjd_Start=%.3f | dT=%.3e]'%(obsStandars['targets'][id].objname,secz[i],obstime,blockDuration[id]))
					seczreq[sindex] = True
					obsStandars['targets'][id].scheduled = True
					session.commit()
					#print obsStandars['obsblock'][id]
					self.addObservation(obsStandars['obsblock'][id],obstime)
					#self.obsTimeMask[obsMask[id]] = 1.0
			#print self.obsTimeBins[obsMask[id]]
			#print

		#print i
		return 0 #targets

	############################################################################

	def addObservation(self,block,obstime):
	
		session = Session()
		
		# Schedule each observing block
		#for i,block in enumerate(obsBlocks):
		
			#imagetype = block.imagetype.upper()

			# Query for targets in that block
		bTargets = session.query(Targets).filter(Targets.id == block.objid)
		blockConfig = session.query(BlockConfig).filter(BlockConfig.pid == block.pid,BlockConfig.bid == block.blockid)

		imtypes = [b.imagetype.upper() for b in blockConfig]
		
		imagetype = "OBJECT" if "OBJECT" in imtypes else "FLAT" if "FLAT" in imtypes else imtypes[0]
		
		programs = []
		
		for i,target in enumerate(bTargets):
			
			objname = target.objname.replace("\"", "").replace(" ", "")
			program = Program(pid = block.pid,blockid=block.blockid,
							  slewAt=obstime)#,exposeAt=obstime)
			
			position  = Position.fromRaDec(target.targetRa,target.targetDec,'J%.0f'%target.targetEpoch)

			self.log.info("# program: %s" % program.pid)

			if imagetype == "OBJECT":
				if position:
					program.actions.append(Point(targetRaDec=position))
				else:
					program.actions.append(Point(targetName=objname))

			if imagetype == "FLAT":
				site = self._remoteManager.getProxy("/Site/0")
				flatPosition = Position.fromAltAz(site['flat_alt'], site['flat_az'])
				program.actions.append(Point(targetAltAz=flatPosition))


			for exp in blockConfig:

				filter, exptime, frames = exp.filter,exp.exptime,exp.nexp

				if exp.imagetype.upper() in ("OBJECT", "FLAT"):
					shutter = "OPEN"
				else:
					shutter = "CLOSE"

				if exp.imagetype.upper() == "BIAS":
					exptime = 0

				if exp.imagetype.upper() in ("BIAS", "DARK"):
					filter = None

				self.log.info("%s %s %s filter=%s exptime=%s frames=%s" % (imagetype, objname, str(position), filter, exptime, frames))

				program.actions.append(Expose(shutter=shutter,
											  filename="%s-%s-$DATE-$TIME" % (block.pid,objname.replace(" ", "")),
											  filter=filter,
											  frames=frames,
											  exptime=exptime,
											  imageType=exp.imagetype.upper(),
											  objectName=objname))

			self.log.info("")
			programs.append(program)

		session.add_all(programs)
		session.commit()


	############################################################################

################################################################################

def checkQueue(queue):
	'''
Auxiliary function: Checks if queue makes sense. Basically check if there are 
overlapping observations and return True or False
	'''

	if len(queue) == 0:
		return False
	asort = queue['start'].argsort()
	queue['start'] = queue['start'][asort]
	queue['end'] = queue['end'][asort]

	check = queue['end'][:-1] - queue['start'][1:] > 0

	return check.any()

################################################################################












