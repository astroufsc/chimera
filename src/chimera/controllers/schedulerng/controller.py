from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException, ObjectNotFoundException

from chimera.controllers.schedulerng.machine import Machine
from chimera.controllers.schedulerng.sequential import SequentialScheduler
from chimera.controllers.schedulerng.states import State

from chimera.interfaces.camera  import Shutter, Binning, Window

import chimera.core.log
import logging
import threading
from elixir import session

class Controller(ChimeraObject):
    __config__ = {"telescope"   : "/Telescope/0?driver=/FakeTelescope/0",
                  "camera"      : "/Camera/0?driver=/FakeCamera/0",
                  "filterwheel" : "/FilterWheel/0?driver=/FakeFilterWheel/0",
                  "focuser"     : "/Focuser/0?driver=/FakeFocuser/0",
                  "dome"        : "/Dome/0?driver=/FakeDome/0"}

    def __init__(self):
        ChimeraObject.__init__(self)
        self.machine = Machine(SequentialScheduler(), self)
        self.proxies = {}

    def __start__(self):
        # try to get proxies
        try:
            #FIXME: Proxies should be gotten in machine thread; not here! and preferably before each obs.
            # alternatively, need to call proxy._transferThread() in new thread
            #Reason to get in destination thread is to avoid need to restart entire scheduler in case
            #remote manager dies for any reason and needs to be restarted. Otherwise, NameErrors may abound
            self.proxies["telescope"]   = self.getManager().getProxy(self["telescope"])
            self.proxies["camera"]      = self.getManager().getProxy(self["camera"])
            self.proxies["filterwheel"] = self.getManager().getProxy(self["filterwheel"])
            self.proxies["focuser"]     = self.getManager().getProxy(self["focuser"])
            self.proxies["dome"]        = self.getManager().getProxy(self["dome"])
            self.proxies["scheduler"]   = self.getProxy()

            self.machine.proxies = self.proxies
            
            self.proxies['telescope'].startTracking()
            self.proxies['dome'].track()
            self.proxies['dome'].openSlit()
        except ObjectNotFoundException, e:
            raise ChimeraException("Cannot start scheduler. %s." % e)

    def control(self):
        self.machine.start()
        return False # that's all folks; control is only run once

    def __stop__ (self):
        self.log.debug('Attempting to stop machine')
        self.machine.state(State.SHUTDOWN)
        self.log.debug('Attempted to stop machine')
        session.flush()
        
    def process(self, exposure):
        self.proxies['telescope']._transferThread()
        self.proxies['dome']._transferThread()
        self.proxies['camera']._transferThread()
        self.proxies['filterwheel']._transferThread()
        if exposure.observation==None:            
            raise ObjectNotFoundException('Unable to find associated observation')
        self.log.debug('Attempting to slew telescope to ' + exposure.observation.targetPos.__str__())
        self.proxies['telescope'].slewToRaDec(exposure.observation.targetPos)
        while (self.proxies['telescope'].isSlewing() | self.proxies['dome'].isSlewing()):
            self.log.debug('Waiting for slew to finish. Dome: ' + self.proxies['dome'].isSlewing().__str__() + '; Tel:' + self.proxies['telescope'].isSlewing().__str__())
            time.sleep(1)
        self.log.debug('Telescope Slew Complete')
        self.log.debug('Setting filterwheel to ' + exposure.filter.__str__())
        self.proxies['filterwheel'].setFilter(exposure.filter)
        while (self.proxies['filterwheel'].getFilter() != exposure.filter):
            self.log.debug('Waiting for filterwheel to finish. Current: ' + self.proxies['filterwheel'].getFilter().__str__() + '; Wanted: ' + exposure.filter.__str__())
            time.sleep(1)
        self.log.debug('Exposing...' + self.proxies['camera'].__str__() + '::' + self.proxies['camera'].getDriver().__str__())
        files = self.proxies['camera'].expose(exposure.duration,
                frames=exposure.duration, interval=0.0,
                shutter=exposure.shutterOpen,
                binning=(exposure.binX, exposure.binY),
                window=(exposure.windowXCtr, exposure.windowYCtr, exposure.windowWidth, exposure.windowHeight),
                filename="$HOME/images/$date.fits")
        #TODO: set headers on files in files
