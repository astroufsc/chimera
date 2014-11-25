
'''
    A queue executer for chimera. This is just like a sequential executor with
    the difference that it will 
'''

from chimera.controllers.scheduler.ischeduler import IScheduler
from chimera.controllers.scheduler.model import Session, Program, Projects, BlockConfig

from chimera.core.site import (Site, datetimeFromJD)

from sqlalchemy import (desc, asc)

import chimera.core.log
import logging

log = logging.getLogger(__name__)

from Queue import PriorityQueue

class QueueScheduler (IScheduler):
    
    def __init__ (self):
        self.rq = None
        self.machine = None
    
    def reschedule (self, machine):
        
        self.machine = machine
        self.rq = PriorityQueue(-1)
        
        session = Session()
        programs = session.query(Program).join(Projects).order_by(desc(Program.exposeAt)).filter(Program.finished == False).filter(Projects.priority == 0).all()
        
        if not programs:
            return
        
        log.debug("rescheduling, found %d runnable programs" % len(list(programs)))
        
        for itr,program in enumerate(programs):
			self.rq.put((itr,program))
        
        machine.wakeup()
    
    def next (self):
        if not self.rq.empty():
            log.debug("qqqqqqqqqqqqqqqqqqqq self.rq %s",self.rq)
			# Get next program
            prt,program = self.rq.get()
            # Get alternate program and program duration (lenght)
            site = Site()
            nowmjd=site.MJD()
            altprogram,aplen = self.getAlternateProgram(nowmjd)
            #return program
            if aplen < 0:
				log.debug('Using normal program (aplen < 0)...')
				return program
			
            # If alternate program fits will send it instead
			
            if program.slewAt:
				waittime=(program.slewAt-nowmjd)*86.4e3
				if waittime>aplen:
					log.debug('Using alternate program...')
					# put program back with same priority
					self.rq.put((prt,program))
					# return alternate program
					return altprogram
            log.debug('Using normal program (waitime)...')
            return program
        
        return None
    
    def done (self, task, error=None):
        
        if error:
            log.debug("Error processing program %s." % str(task))
            log.exception(error)
        else:
            task.finished = True
        
        self.rq.task_done()
        self.machine.wakeup()


    def getAlternateProgram(self,nowmjd):
	
		session = Session()

		q_plist = session.query(Projects).filter(Projects.priority > 0)
		
		plist = np.unique(np.array([q.priority for q in q_plist]))
		
		for priority in plist:
		
			program1 = session.query(Program).join(Projects).order_by(desc(Program.exposeAt)).filter(Program.finished == False).filter(Projects.priority == priority).filter(Program.exposeAt > nowmjd).first()

			program2 = session.query(Program).join(Projects).order_by(asc(Program.exposeAt)).filter(Program.finished == False).filter(Projects.priority == priority).filter(Program.exposeAt < nowmjd).first()

			if not program1 and not program2:
				log.debug('No program in alternate queue %i'%priority)
				continue
				#return None,-1
			elif not program1:
				log.debug('No program1 in alternate queue %i'%priority)
				dT = 0
				block = session.query(BlockConfig).filter(BlockConfig.pid == program2.pid,BlockConfig.bid == program2.blockid)
				for t in block:
					dT += t.nexp * t.exptime

				return program2,dT
			elif not program2:
				log.debug('No program2 in alternate queue %i'%priority)
				dT = 0
				block = session.query(BlockConfig).filter(BlockConfig.pid == program1.pid,BlockConfig.bid == program1.blockid)
				for t in block:
					dT += t.nexp * t.exptime

				return program1,dT
				
			log.debug('Found 2 suitable programs in alternate queue %i'%priority)
			
			wtime1 = (program1.slewAt-nowmjd)
			wtime2 = (nowmjd-program2.slewAt)

			if wtime1 < wtime2:
				log.debug('Program1 closer')
				dT = 0
				block = session.query(BlockConfig).filter(BlockConfig.pid == program1.pid,BlockConfig.bid == program1.blockid)
				for t in block:
					dT += t.nexp * t.exptime

				return program1,dT
			else:
				log.debug('Program2 closer')
				dT = 0
				block = session.query(BlockConfig).filter(BlockConfig.pid == program2.pid,BlockConfig.bid == program2.blockid)
				for t in block:
					dT += t.nexp * t.exptime

				return program2,dT
	
		return None,-1
