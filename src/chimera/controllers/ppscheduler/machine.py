import chimera.core.log

from chimera.controllers.scheduler.states import State
from chimera.controllers.scheduler.model import Session, Program
from chimera.controllers.scheduler.status import SchedulerStatus


from chimera.core.exceptions import ProgramExecutionException, ProgramExecutionAborted

from chimera.core.site import Site 

#from sandbox import Sandbox, SandboxConfig
#from sandbox.proxy import proxy

import ephem
import math

import threading
import logging

import time

log = logging.getLogger(__name__)

def zenithdistance(target):
    return 0.5*math.pi-target.alt

def airmass(target):
    return 1.0/math.cos(zenithdistance(target)) 

def getobserver(siteproxy):
    site = ephem.Observer()
    site.lat  = siteproxy["latitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
    site.long = siteproxy["longitude"].strfcoord('%(d)d:%(m)d:%(s).2f')
    site.elev = siteproxy['altitude']
    site.date = siteproxy.ut()
    site.epoch='2000/1/1 00:00:00'
    return site

def proxyNamespace(d):
    return dict((str(k), proxy(v)) for k, v in d.iteritems())
        
#def wrapeval(expr,globs,locs):
#    subglobs = proxyNamespace(globs)
#    sublocs = proxyNamespace(locs)
#    return eval(expr,subglobs,sublocs)
#    try:
#        ret=eval(expr,subglobs,sublocs)
#    except:
#        ret=False
#    return ret

def evalexpr(expr,globs,locs):
    return eval(expr,globs,locs)
    try:
        ret=eval(expr,globs,locs)
    except:
        ret=False
    return ret


class Machine(threading.Thread):
    
    __state = None
    __stateLock = threading.Lock()
    __wakeUpCall = threading.Condition()
    
    def __init__(self, scheduler, executor, controller, site):
        threading.Thread.__init__(self)

        self.scheduler = scheduler
        self.executor = executor
        self.controller = controller

        self.currentProgram = None

        self.setDaemon(False)
        
        self.site=site

    def state(self, state=None):
        self.__stateLock.acquire()
        try:
            if not state: return self.__state
            if state == self.__state: return
            self.controller.stateChanged(state, self.__state)
            log.debug("Changing state, from %s to %s." % (self.__state, state))
            self.__state = state
            self.wakeup()
        finally:
            self.__stateLock.release()
            
    

    def run(self):
        log.info("Starting scheduler machine")
        self.state(State.OFF)

        # inject instruments on handlers
        self.executor.__start__()
        #sandbox=Sandbox()

        while self.state() != State.SHUTDOWN:

            if self.state() == State.OFF:
                log.debug("[off] will just sleep..")
                self.sleep()

            if self.state() == State.START:
                log.debug("[start] database changed, rescheduling...")
                self.scheduler.reschedule(self)
                self.state(State.IDLE)

            if self.state() == State.IDLE:

                log.debug("[idle] looking for something to do...")

                # find something to do
                #found=False
                program = self.scheduler.next()
                
                #Obtain the whole sequence of programs in the while loop
                if program:
                    log.debug("[idle] there is something to do, processing...")
                    if program.whileindex<0:
                        log.debug("[idle] while loop found, processing...")
                        log.debug("[idle] loop condition:'"+program.whilecond+"'")
                    print "Actions:"
                    for action in program.actions: #Find out the pointing target
                        if action.action_type=="Point":
                            point=action
                    if point.targetRaDec:
                        #ra,dec=point.targetRaDec.split()
                        targets=str(point.targetRaDec)#Position.fromRaDec(ra=ra,dec=dec)
                    if point.targetName:
                        targets=str(Simbad.lookup(point.targetName))
                    sun=ephem.Sun()
                    moon=ephem.Moon()
                    site=getobserver(self.site)
                    sun.compute(site)
                    moon.compute(site)
                    print "Target:"
                    print targets,type(targets)
                    ra,dec=targets.split()
                    target=ephem.readdb("target,f,"+ra+","+dec+",,2000")
                    target.compute(site)
                    globs={'target':target,'sun':sun,'moon':moon,'ephem':ephem,'math':math,'time':time,'observer':site,'site':self.site,'airmass':airmass,'zenithdistance':zenithdistance}
                    print site
                    locs=globs
                    whileres=evalexpr(program.whilecond,globs,locs)
                    if whileres:
                    #if sandbox._call(wrapeval,(program.whilecond,globs,locs),{}):
                        if program.whileindex<0:
                            log.debug("[idle] while condition evaluated to: %s",whileres)    
                        log.debug("[idle] program slew start %s",program.slewAt)
                        log.debug("[idle] program exposure start %s",program.exposeAt)
                        self.state(State.BUSY)
                        self.currentProgram = program
                        self.scheduler.put_back(program)
                        self._process(program)
                    else:
                        log.debug("[idle] while condition evaluated to: %s",whileres)
                    continue

#                if program:
#                    found=True
#                    log.debug("[idle] there is something to do, processing...")
#                    programsinwhile=[]
#                    while True:
#                        programsinwhile.append(program)
#                        if (program.whileindex >= -1):
#                            break
#                        program = self.scheduler.next()
#                        
#                while True:
#                    condition_failed=False
#                    log.debug("[idle]hhhhhhhhhwhile loop index:")
#                    if program.whileindex<0:
#                        log.debug("[idle] while loop found, processing...")
#                        log.debug("[idle] loop condition:")
#                        log.debug(program.whilecond)
#                    print "programsinwhile:",len(programsinwhile)
#                    for program in programsinwhile:
#                        print program.name
#                        print program.whileindex
#                        print program.whilecond
#                        log.debug("[idle] evaluating loop condition")
#                        if eval(program.whilecond):
#                            log.debug("[idle] program slew start %s",program.slewAt)
#                            log.debug("[idle] program exposure start %s",program.exposeAt)
#                            self.state(State.BUSY)
#                            self.currentProgram = program
#                            self._process(program)
#                        else:
#                            condition_failed=True
#                            log.debug("[idle] while loop condition evaluated to False, getting out of loop")
#                            break
#                    if condition_failed or program.whileindex==0:
#                        break
#                
#                if found:
#                    continue

                # should'nt get here if any task was executed
                log.debug("[idle] there is nothing to do, going offline...")
                self.currentProgram = None
                self.state(State.OFF)

            elif self.state() == State.BUSY:
                log.debug("[busy] waiting tasks to finish..")
                self.sleep()

            elif self.state() == State.STOP:
                log.debug("[stop] trying to stop current program")
                self.executor.stop()
                self.state(State.OFF)

            elif self.state() == State.SHUTDOWN:
                log.debug("[shutdown] trying to stop current program")
                self.executor.stop()
                log.debug("[shutdown] should die soon.")
                break

        log.debug('[shutdown] thread ending...')

    def sleep(self):
        self.__wakeUpCall.acquire()
        log.debug("Sleeping")
        self.__wakeUpCall.wait()
        self.__wakeUpCall.release()

    def wakeup(self):
        self.__wakeUpCall.acquire()
        log.debug("Waking up")
        self.__wakeUpCall.notifyAll()
        self.__wakeUpCall.release()

    def restartAllPrograms(self):
        session = Session()

        programs = session.query(Program).all()
        for program in programs:
            program.finished = False

        session.commit()
        
    def _process(self, program):

        def process ():

            # session to be used by executor and handlers
            session = Session()

            task = session.merge(program)

            log.debug("[start] %s" % str(task))

            
            nowmjd=self.site.MJD()
            log.debug("[start] Current MJD is %f",nowmjd)
            if program.slewAt:
                waittime=(program.slewAt-nowmjd)*86.4e3
                if waittime>0.0:
                    log.debug("[start] Waiting until MJD %f to start slewing",program.slewAt)
                    log.debug("[start] Will wait for %f seconds",waittime)
                    time.sleep(waittime)
                else:
                    log.debug("[start] Specified slew start MJD %s has already passed; proceeding without waiting",program.slewAt)
            else:
               log.debug("[start] No slew time specified, so no waiting") 
            log.debug("[start] Current MJD is %f",self.site.MJD())
            log.debug("[start] Proceeding since MJD %f should have passed",program.slewAt) 
            
            try:
                self.executor.execute(task)
                log.debug("[finish] %s" % str(task)) 
                self.scheduler.done(task)
                self.controller.programComplete(program, SchedulerStatus.OK)
                self.state(State.IDLE)
            except ProgramExecutionException, e:
                self.scheduler.done(task, error=e)
                self.controller.programComplete(program, SchedulerStatus.ERROR, str(e))
                self.state(State.IDLE)
                log.debug("[error] %s (%s)" % (str(task), str(e)))
            except ProgramExecutionAborted, e:
                self.scheduler.done(task, error=e)
                self.controller.programComplete(program, SchedulerStatus.ABORTED, "Aborted by user.")
                self.state(State.OFF)
                log.debug("[aborted by user] %s" % str(task))

            session.commit()

        t = threading.Thread(target=process)
        t.setDaemon(False)
        t.start()
