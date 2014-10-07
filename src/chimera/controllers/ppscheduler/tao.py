#import chimera.core.log

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

import logging

log = logging.getLogger(__name__)

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

	__config__ = {	'stdFlag': '',
					'sciFlag': '',
					'stdUser'    : '',
					'sciUser'    : '',
					'stdFile'    : '',
					'sciFile'    : '',
					'stdExpTime' : [0],
					'sciExpTime' : [0],
					'PATH'	     : '',
					'sitelat'    : '',
					'sitelong'   : '',
					'sunMaxAlt'  : '',
					'filters'    : ['clear'],
					'nfilters'   : 1,
					'stdMaxAirmass' : 1.8}

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
		
		if os.path.exists(os.path.join(os.path.expanduser('~/.chimera'),'tao.cfg')):
			config.read(os.path.join(os.path.expanduser('~/.chimera'),'tao.cfg'))
		else:
			log.warning('No user defined configuration found at %s. Using default values.'%(os.path.join(os.path.expanduser('~/.chimera'),'tao.cfg')))
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

		self.stdMaxAirmass = float(config.get('TargetsInfo','stdMaxAirmass'))

		#
		# These are time bins, which breaks the night in timely intervals. Bins is the time at the begining of the bin
		# and Mask is percent full. 
		self.obsTimeBins = []
		self.obsTimeMask = []

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
		
		nightstart = _skysub.jd_sun_alt(self.sunMaxAlt, jd, self.sitelat, self.sitelong)
		nightend   = _skysub.jd_sun_alt(self.sunMaxAlt, jd+0.5, self.sitelat, self.sitelong)
		
		log.debug('Nigh Start @JD= %.3f # Night End @JD = %.3f'%(nightstart,nightend))
		
		tbin = np.max([np.max(self.sciExpTime),np.max(self.stdExpTime)])*self.nfilters/60./60./24.

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

				log.info('Selecting %s'%(targets[stg]))
				
				# Marking target as schedule
				tst = session.query(Targets).filter(Targets.id == targets[stg].id)

				for t in tst:
					t.scheduled = True
					session.commit()
					self.addObservation(t,time)
				
				self.obsTimeMask[tbin] = 1.0
			else:
				log.debug('Bin %3i @mjd=%.3f already filled up with observations. Skipping...'%(tbin,time-2400000.5))
				
		#print i
		return 0 #targets

	####################################################################################################################################

	def selectStandardTargets(self,nstars=3,nairmass=3):
		'''
		Based on configuration parameters, select 'nstars' standard stars to run scheduler on a specified Julian Day. Ideally you 
		will select standard stars before your science targets so not to have a full queue. Usually standard stars are observed 
		more than once a night at different airmasses. The user can control this parameter with nairmass and the script will try
		to take care of the rest. 
		'''

		session = Session()
		
		# First of all, standard stars can be obsered multiple times in sucessive nights. I will mark all
		# stars an unscheduled.
		targets = session.query(Targets).filter(Targets.scheduled == True).filter(Targets.type == self.stdFlag)
		for target in targets:
			target.scheduled = False
			session.commit()
		
		# [To be done] Reject objects that are close to the moon

		# Selecting standard stars is not only searching for the higher in that time but select stars than can be observed at 3
		# or more (nairmass) different airmasses. It is also important to select stars with different colors (but this will be
		# taken care in the future).

		if nairmass*nstars > len(self.obsTimeBins):
			log.warning('Requesting more stars/observations than it will be possible to schedule. Decreasing number of requests to fit in the night.')
			nstars = len(self.obsTimeBins)/nairmass

		obsStandars = np.zeros(len(self.obsTimeBins))-1 # first selection of observable standards

		for tbin,time in enumerate(self.obsTimeBins):

			if self.obsTimeMask[tbin] < 1.0:
				# 1 - Select objects from database that where not scheduled yet (standard stars may be repited)
				#     that fits our observing night
				targets = session.query(Targets).filter(Targets.scheduled == 0).filter(Targets.type == self.stdFlag)
			
				lst = _skysub.lst(time,self.sitelong) #*360./24.
				alt = np.array([_skysub.altit(target.targetDec,lst - target.targetRa,self.sitelat)[0] for target in targets])
				stg = alt.argmax()

				log.info('Selecting %s'%(targets[stg]))
				
				# Marking target as schedule
				tst = session.query(Targets).filter(Targets.id == targets[stg].id)

				for t in tst:
					t.scheduled = True
					session.commit()
					obsStandars[tbin] = t.id
				
			else:
				log.info('Bin already filled up with observations. Skipping...')

		if len(obsStandars[obsStandars >= 0]) < nstars:
			log.warning('Could not find %i suitable standard stars in catalog. Only %i where found.'%(nstars,len(obsStandars[obsStandars >= 0])))
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
					log.info('Requesting observations of %s @airmass=%4.2f @mjd=%.3f...'%(target.name,secz[i],obstime-2400000.5))
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

	def targets(self):
		'''
		After selecting targets, you can generate a list of potential targets to run the scheduler.
		'''
		
		import subprocess
		
		session = Session()

		request = os.path.join(self.PATH,'targets/request.stg')
		
		fp1 = open(os.path.join(self.PATH,'targets/Fixed.txt'),'w')
		fp2 = open(request,'w')

		# Write header
		fp1.write('''P|Designation |    RA     |    dec    |mag.
-|------------|hh mm ss.ss|sdd mm ss.s|nn.n
''')

		config = {	'name' : '',
					'user' : '',
					'nimages' : 1,
					'expt' : 0,
					'filter' : '',
					'time' : ''}


		for obstype in [self.stdFlag,self.sciFlag]:
		
			targets = session.query(Targets,Program).join((Program,Targets.id==Program.tid)).filter(Targets.type == obstype).order_by(Targets.name)
			tobs = []
			
			tname = ''
			FlagFilterClear = True
			for target,program in targets:

				p = Position.fromRaDec(target.targetRa,target.targetDec)
				ra = p.ra.HMS
				dec = p.dec.DMS

				#
				# Write Fixed.txt
				#
				objname = '%12s'%(target.name).replace(' ','_')
				objname = objname.replace(' ','_')
				fp1.write('%1s %s %02.0f %02.0f %05.2f %+03.0f %02.0f %04.1f %04.1f\n'%(	target.type,
																			objname,
																			ra[1],
																			ra[2],
																			ra[3],
																			dec[0]*dec[1],
																			dec[2],
																			dec[3],target.targetMag))

				#
				# Write stg file with observation requests
				#
				config['name'] = objname
				config['user'] = self.stdUser
				filterExpt = self.stdExpTime
				if target.type == self.sciFlag:
					config['user'] = self.sciUser
					filterExpt = self.sciExpTime
					config['time'] = ''
				dt = np.max(filterExpt)*self.nfilters/60./60./24.
				if target.type ==self.stdFlag:
					FlagFilterClear = True
					tname = target.name
					tstart = datetimeFromJD(program.slewAt + 2400000.5)
					tend = datetimeFromJD(program.slewAt+dt + 2400000.5)
					config['time'] = 't>%s t<%s'%(tstart.strftime('%y%m%d-%H:%M'),tend.strftime('%y%m%d-%H:%M'))

				for i in range(self.nfilters):
					config['expt'] = filterExpt[i]
					config['filter'] = self.filters[i]
					tstart = datetimeFromJD(program.slewAt + 2400000.5)
					tend = datetimeFromJD(program.slewAt+dt*1.1 + 2400000.5)
					
					fp2.write('%(name)12s; %(user)s %(nimages)ii exp=%(expt).2f opt filter=%(filter)s %(time)s\n'%config)

		fp1.close()
		fp2.close()
		
		#
		# Calling targets from TAO to generate targets list.
		#
		fp1 = open(os.path.join(self.PATH,'targets/targets.log'),'w')
		bin = os.path.expanduser(os.path.join(self.PATH,'targets/targets'))
		runTargets = subprocess.Popen([bin,'-s',request],stdout=fp1,stderr=fp1)
		
		runTargets.wait()
		fp1.close()
		
		return 0

	####################################################################################################################################

	def addObservation(self,target,obstime):
	
		session = Session()
		
		lineRe = re.compile('(?P<coord>(?P<ra>[\d:-]+)\s+(?P<dec>\+?[\d:-]+)\s+(?P<epoch>[\dnowNOWJjBb\.]+)\s+)?(?P<imagetype>[\w]+)'
                            '\s+(?P<objname>\'([^\\n\'\\\\]|\\\\.)*\'|"([^\\n"\\\\]|\\\\.)*"|([^ \\n"\\\\]|\\\\.)*)\s+(?P<exposures>[\w\d\s:\*\(\),]*)')
		programs = []
		
		entryFormat = '%(ra)s %(dec)s %(epoch)s %(obstype)s %(name)s %(exposures)s'
		
		p = Position.fromRaDec(target.targetRa,target.targetDec)
		ra = p.ra.HMS
		dec = p.dec.DMS
		
		filterExpt = self.sciExpTime
		if target.type == self.stdFlag:
			filterExpt = self.stdExpTime

		exposures = '1*('

		for i in range(self.nfilters):
			exposures = exposures+'%s:%.0f, '%(self.filters[i],filterExpt[i])

		exposures = exposures[:-2]
		exposures += ')'
		
		infos = {	'ra' : '%02.0f:%02.0f:%02.0f'%(ra[1],ra[2],ra[3]),
					'dec': '%+03.0f:%02.0f:%02.0f'%(dec[0]*dec[1],dec[2],dec[3]),
					'epoch' : 'J%.0f'%target.targetEpoch,
					'obstype' : 'OBJECT',
					'name' :target.name,
					'exposures' : exposures
					}

		i = 0
		line = entryFormat%infos
		
		matchs = lineRe.search(line)
		params = matchs.groupdict()
		
		position = None
		objname  = None

		if params.get("coord", None):
			position  = Position.fromRaDec(str(params['ra']), str(params['dec']), params['epoch'])

		imagetype = params['imagetype'].upper()
		objname   = params['objname'].replace("\"", "")

		multiplier, exps = params['exposures'].split("*")
		try:
			multiplier = int(multiplier)
		except ValueError:
			multiplier = 1

		exps = exps.replace("(", "").replace(")", "").strip().split(",")

		mjd = obstime - 2400000.5
		for i in range(multiplier):

			program = Program(tid = target.id ,name="%s-%03d" % (objname.replace(" ", ""), i),
                              slewAt=mjd,exposeAt=mjd+1./60./24.)

			log.info("# program: %s" % program.name)

			if imagetype == "OBJECT":
				if position:
					program.actions.append(Point(targetRaDec=position))
				else:
					program.actions.append(Point(targetName=objname))

			if imagetype == "FLAT":
				site = self._remoteManager.getProxy("/Site/0")
				flatPosition = Position.fromAltAz(site['flat_alt'], site['flat_az'])
				program.actions.append(Point(targetAltAz=flatPosition))

			#if i == 0:
			#    program.actions.append(AutoFocus(start=1500, end=3000, step=250, filter="R", exptime=10))
			#    program.actions.append(PointVerify(here=True))

			for exp in exps:
				if exp.count(":") > 1:
					filter, exptime, frames = exp.strip().split(":")
				else:
					filter, exptime = exp.strip().split(":")
					frames = 1

				if imagetype in ("OBJECT", "FLAT"):
					shutter = "OPEN"
				else:
					shutter = "CLOSE"

				if imagetype == "BIAS":
					exptime = 0

				if imagetype in ("BIAS", "DARK"):
					filter = None

				log.info("%s %s %s filter=%s exptime=%s frames=%s" % (imagetype, objname, str(position), filter, exptime, frames))

				program.actions.append(Expose(shutter=shutter,
											  filename="%s-$DATE-$TIME" % objname.replace(" ", ""),
											  filter=filter,
											  frames=frames,
											  exptime=exptime,
											  imageType=imagetype,
											  objectName=objname))
			log.info("")
			programs.append(program)

		session.add_all(programs)
		session.commit()

