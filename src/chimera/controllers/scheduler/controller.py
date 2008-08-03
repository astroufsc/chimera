from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException, ObjectNotFoundException

from chimera.controllers.scheduler.machine import Machine
from chimera.controllers.scheduler.sequential import SequentialScheduler
from chimera.controllers.scheduler.states import State

from chimera.interfaces.camera  import SHUTTER_OPEN, SHUTTER_CLOSE#, Binning, Window 

from chimera.controllers.imageserver.imagerequest import ImageRequest

import chimera.core.log
import logging
import threading
from elixir import session
import time
import Pyro.util

class Controller(ChimeraObject):
    __config__ = {"telescope"   : "/Telescope/0",
                  "camera"      : "/Camera/0",
                  "filterwheel" : "/FilterWheel/0",
                  "focuser"     : "/Focuser/0",
                  "dome"        : "/Dome/0",
                  'site'        : '/Site/0',
                  'camTemp'     : -10,
                  'camTempEnable': False,
                  'camTempWait' : True,
                  'allowDomeOpen': True,
                  }

    def __init__(self):
        ChimeraObject.__init__(self)
        self.machine = Machine(SequentialScheduler(), self)
        self.proxies = {}
        self.hostPort=''

    def __start__(self):
        mgr = self.getManager()
        self.hostPort = mgr.getHostname() + ':' + str(mgr.getPort())

        # try to get proxies
        try:
            #FIXME: Proxies should be gotten in machine thread; not here! and preferably before each obs.
            # alternatively, need to call proxy._transferThread() in new thread
            #Reason to get in destination thread is to avoid need to restart entire scheduler in case
            #remote manager dies for any reason and needs to be restarted. Otherwise, NameErrors may abound
#            self.proxies["telescope"]   = self.getManager().getProxy(self["telescope"])
#            self.proxies["camera"]      = self.getManager().getProxy(self["camera"])
#            self.proxies["filterwheel"] = self.getManager().getProxy(self["filterwheel"])
#            self.proxies["focuser"]     = self.getManager().getProxy(self["focuser"])
#            self.proxies["dome"]        = self.getManager().getProxy(self["dome"])
#            self.proxies["scheduler"]   = self.getProxy()
#
#            self.machine.proxies = self.proxies
            
            mgr = self.getManager()
            tel = mgr.getProxy(self['telescope'])
            dome = mgr.getProxy(self['dome'])
            camera = mgr.getProxy(self['camera'])
            
            tel.startTracking()
            if self['allowDomeOpen']:
                dome.openSlit()
            dome.track()
            if self['camTempEnable']:
                self.log.debug('Starting to cool camera to %i ...' % self['camTemp'])
                camera.startCooling(self['camTemp'])
                while (self['camTempWait'] and abs(camera.getTemperature() - self['camTemp']) > 1):
                    self.log.debug('Waiting for camera to reach setpoint temperature (current: %i, wanted: %i)...' % (camera.getTemperature(),self['camTemp']))
                    time.sleep(2)
                    
        except ObjectNotFoundException, e:
            raise ChimeraException("Cannot start scheduler. %s." % e)

    def control(self):
        self.machine.start()
        return False # that's all folks; control is only run once

    def __stop__ (self):
        self.log.debug('Attempting to stop machine')
        self.machine.state(State.SHUTDOWN)
        self.log.debug('Attempted to stop machine')
        if self['camTempEnable']:
            self.getManager().getProxy(self['camera']).stopCooling()
        session.flush()
        
    def process(self, exposure):
        self.log.debug('Acquiring proxies...')
        telescope   = self.getManager().getProxy(self['telescope'])
        dome        = self.getManager().getProxy(self['dome'])
        camera      = self.getManager().getProxy(self['camera'])
        filterwheel = self.getManager().getProxy(self['filterwheel'])
        
        observation = exposure.observation
        if observation == None:
            raise ObjectNotFoundException('Unable to find associated observation')

        program = observation.program
        if program == None:
            raise ObjectNotFoundException('Unable to find associated program')
        
        
        self.log.debug('Attempting to slew telescope to ' + observation.targetPos.__str__())
        telescope.slewToRaDec(observation.targetPos)
        self.log.debug('Setting filter to ' + str(exposure.filter) + '...')
        filterwheel.setFilter(str(exposure.filter))
        while (telescope.isSlewing() or dome.notSyncWithTel()):
            self.log.debug('Waiting for slew to finish. Dome: ' + dome.isSlewing().__str__() + '; Tel:' + telescope.isSlewing().__str__())
            time.sleep(1)
        self.log.debug('Telescope Slew Complete')
        #FIXME: filterwheel doesn't respond properly!
        #while (str(filterwheel.getFilter()) != str(exposure.filter)):
        #    self.log.debug('Waiting for filterwheel to finish. Current: ' + filterwheel.getFilter().__str__() + '; Wanted: ' + exposure.filter.__str__())
        #    filterwheel.setFilter(str(exposure.filter))
        #    time.sleep(1)
        if (str(filterwheel.getFilter()) != str(exposure.filter)):
            self.log.warning('Filterwheel didn\'t behave as expected. Current: ' + filterwheel.getFilter().__str__() + '; Wanted: ' + exposure.filter.__str__())
        self.log.debug('Filter set')
        
        self.log.debug('Generating exposure request..')
        
        if exposure.shutterOpen:
            shutter=('Open', SHUTTER_OPEN)
        else:
            shutter=('Closed', SHUTTER_CLOSE)
        
        ir = ImageRequest(
                          exp_time = exposure.duration,
                          shutter=shutter,
                          frames = exposure.frames,
                          headers = [
                                     ('OBJECT', str(observation.targetName), 'Object name'),
                                     ('TRGT_RA', observation.targetPos.ra.__str__(), 'Target RA'),
                                     ('TRGT_DEC', observation.targetPos.dec.__str__(), 'Target DEC'),
                                     ('PROGRAM', str(program.caption), 'Program Name'),
                                     ('PROG_PI', str(program.pi), 'Program\'s PI'),
                                     ],
                          image_type = str(exposure.imageType),
                          metadatapre = [
                                         self.hostPort+self['telescope'],
                                         self.hostPort+self['camera'],
                                         self.hostPort+self['filterwheel'],
                                         self.hostPort+self['focuser'],
                                         self.hostPort+self['dome'],
                                         self.hostPort+self['site'],
                                         ]
                          )
        self.log.info('Running exposure ' + str(ir))
        try:
            camera.expose(ir)
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
#        self.proxies['telescope']._transferThread()
#        self.proxies['dome']._transferThread()
#        self.proxies['camera']._transferThread()
#        self.proxies['filterwheel']._transferThread()
#        if exposure.observation==None:            
#            raise ObjectNotFoundException('Unable to find associated observation')
#        self.log.debug('Attempting to slew telescope to ' + exposure.observation.targetPos.__str__())
#        self.proxies['telescope'].slewToRaDec(exposure.observation.targetPos)
#        while (self.proxies['telescope'].isSlewing() | self.proxies['dome'].isSlewing()):
#            self.log.debug('Waiting for slew to finish. Dome: ' + self.proxies['dome'].isSlewing().__str__() + '; Tel:' + self.proxies['telescope'].isSlewing().__str__())
#            time.sleep(1)
#        self.log.debug('Telescope Slew Complete')
#        self.log.debug('Setting filterwheel to ' + exposure.filter.__str__())
#        self.proxies['filterwheel'].setFilter(exposure.filter)
#        while (self.proxies['filterwheel'].getFilter() != exposure.filter):
#            self.log.debug('Waiting for filterwheel to finish. Current: ' + self.proxies['filterwheel'].getFilter().__str__() + '; Wanted: ' + exposure.filter.__str__())
#            time.sleep(1)
#        self.log.debug('Exposing...' + self.proxies['camera'].__str__() + '::' + self.proxies['camera'].getDriver().__str__())
#        files = self.proxies['camera'].expose(exposure.duration,
#                frames=exposure.duration, interval=0.0,
#                shutter=exposure.shutterOpen,
#                binning=(exposure.binX, exposure.binY),
#                window=(exposure.windowXCtr, exposure.windowYCtr, exposure.windowWidth, exposure.windowHeight),
#                filename="$HOME/images/$date.fits")
        #TODO: set headers on files in files
        pass
