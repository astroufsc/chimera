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

# First version: 13/12/2005 @ OBS

import logging
import time
import os
import os.path
import sys
import string

# force pyfits to use numpy
os.environ["NUMERIX"] = "numpy"
import pyfits

from chimera.util.catalog import Object
from chimera.util.output import *
from chimera.util.observation import Observation, ObservationPlan

from chimera.core.version import _chimera_description_

from chimera.core.lifecycle import BasicLifeCycle

class Observer (BasicLifeCycle):

    __options__ = {"camera": "/Camera/0",
		   "telescope": "/Telescope/0",
		   "filterwheel": "/FilterWheel/0",
		   "plan": "obs.plan",
		   "verbose": True}

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):

        self.config += config

        self.cam = self.manager.getInstrument (self.config.camera)
	self.tel = self.manager.getInstrument (self.config.telescope)
	self.fw = self.manager.getInstrument (self.config.filterwheel)

	if not self.cam or not self.tel or not self.fw:
            return False

        return True

    def main (self):

        plan = self.readPlan (self.config.plan)

	if plan:
	    self.executePlan (plan)

    def executePlan(self, plan):

        # diretorio para as imagens deste plano (/diretorio/onde/estah/o/plano/nome-do-plano-data)
        _plan_path = os.path.split(os.path.expanduser(os.path.abspath(plan.filename)))
        plan_directory = '%s-%s' % (os.path.join(_plan_path[0], os.path.splitext(_plan_path[1])[0]),
                                    time.strftime("%Y%m%d-%H%M%S", time.gmtime()))

        save_on_temp = False
        # create dir if doesn't exists
        if not self._createTargetDir (plan_directory):
            save_on_temp = True
            logging.warning ("Couldn't create %s. Trying to save on /tmp." % plan_directory)
			    
        # open log
        plan_log = os.path.join (plan_directory, "%s.%s" % (os.path.splitext(plan.filename)[0], "log"))

        log = logging.getLogger ("chimera.controllers.observer.plan")
        log.propagate = 0        
        logging.getLogger('').setLevel(logging.INFO)

        file_log = logging.FileHandler (plan_log, 'w')
        file_log.setFormatter (logging.Formatter ('%(message)s', '%m-%d %H:%M'))
        file_log.setLevel (logging.INFO)

        log.addHandler (file_log)

	if self.config.verbose:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            log.addHandler(console)


        log.info ("#" * 50)
        log.info ("Starting plan '%s' at %s with %d object(s)" % (plan.filename,
                                                                  time.strftime("%d/%m/%Y %H:%M:%S"),
                                                                  len(plan)))

        count = 1

        for target in plan:

            log.info ("#" * 50)
            log.info ("[%d/%d] %s | %s %s" % (count, len(plan), target.obj.name, target.obj.ra, target.obj.dec))
            log.info ("Number of exposures: %s" % (target.nexp))
            log.info ("Integration time: %s seconds" % (target.exptime))
            log.info ("Filter: %s" % (target.filtername))


	    # 1 SLEW

	    slew_start = time.time ()
	    log.info ("Slew started at %s" % time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(slew_start)))

	    self.tel.slewToRaDec (target.obj.ra, target.obj.dec)

	    tel_position = self.tel.getPosition ()

	    log.info ("Slew finished at %s (%f secs later)" % (time.strftime("%d/%m/%Y %H:%M:%S"), time.time()-slew_start))

	    # 2. FILTER
  

	    filter_start = time.time ()
	    log.info ("Filter selection started at %s" % time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(filter_start)))

	    self.fw.setFilter (target.filtername)

	    filter_position = self.fw.getFilter ()

	    log.info ("Filter selection finished at %s (%f secs later)" % (time.strftime("%d/%m/%Y %H:%M:%S"),
									       time.time()-filter_start))

	    # 3. IMAGE
	    for i in range(int(target.nexp)):

		    img_start = time.time ()
		    log.info ("Exposure #%d started at %s" % (i+1,
								  time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(img_start))))

		    img = self.cam.expose ({"exp_time"	         : int(float(target.exptime)*100),
					    "shutter" 	         : "open",
					    "date_format"	 : "%Y%m%d-%H%M%S",
					    "file_format"	 : "$objname-$date-$num",
					    "directory"	         : plan_directory,
					    "save_on_temp"       : save_on_temp,
					    "seq_num"	         : i+1,
					    "obj_name"           : string.replace (target.obj.name, ' ', '_').lower(),
					    "temp_regulation"    : False})

		    # Add some headers
		    fp = pyfits.open (img, mode="update")
		    hdu = fp[0]

		    headers = [("OBSERVER", "fulano", "observer who acquired the data"),
			       ("ORIGIN", "Observatorio GAS/UFSC", "organization responsible for the data"),
			       ("OBJECT", target.obj.name or "object", "name of observed object"),
			       ("TELESCOP", "Paramount ME", "name of the telescope"),
			       ("AIRMASS", 0, "air mass"),			       
			       ("RA", target.obj.ra or "-99 99 99", "right ascension of the observed object"),
			       ("DEC", target.obj.dec or "-99 99 99", "declination of the observed object"),
			       ("EXPTIME", float(target.exptime) or -1, "exposure time in seconds"),
			       ("EQUINOX", 2000.0, "equinox of celestial coordinate system"),
			       ("EPOCH - OUTDATED", 2000.0, "equinox of celestial coordinate system"),
			       ("FILTER", target.filtername or "unknown", "name of filter used during the observation"),
			       ("CREATOR", _chimera_description_, ""),
			       ("SECPIX", 0.0, "plate scale")]

		    for header in headers:
			    hdu.header.update (*header)

		    fp.flush ()
		    fp.close ()

		    log.info ("Exposure #%d finished at %s (%f secs later)" % (i+1, time.strftime("%d/%m/%Y %H:%M:%S"),
										   time.time()-img_start))

            count += 1

        log.info ("#" * 50)
        log.info ("Finished plan '%s' at %s" % (plan.filename, time.strftime("%d/%m/%Y %H:%M:%S")))

        logging.shutdown ()

    def readPlan (self, planfile):

        try:
            f = open(planfile)

	    plan = ObservationPlan(planfile)

            # for each line
            for line in f.readlines():

                # reject '#' and blank lines
                if (line.strip() == "") or ('#' in line): continue

                # remove \n and unwanted spaces
                target = line.strip().split(" ")

                # make sure that the path it's absolute, if not prepend current dir to the path
                #if(not os.path.isabs(target[7])):
                #    target[7] = os.path.join(os.getcwd(), target[7])

                # create a new observations
                obs = Observation(target)

                # add observation to the plan
                plan.addObservation(obs)

	    return plan

        except IOError,e:
		logging.error ("%s (%s)" % (e.strerror, e.filename))
		return False

    def _createTargetDir (self, path):

	    if os.path.exists (path):
		    return True

	    try:
		    os.mkdir (path)
		    return True
	    except OSError, e:
		    return False

